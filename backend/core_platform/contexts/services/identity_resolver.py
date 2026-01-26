"""Identity Resolution Service for cross-channel customer identification"""

import difflib
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.db.models import Q
from contexts.models import Customer, CustomerIdentifier, Tenant


class IdentityResolver:
    """
    Service for resolving customer identities across channels and preventing duplicates
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.fuzzy_threshold = 0.8  # Similarity threshold for fuzzy matching
    
    def resolve_identity(self, identifiers: List[Dict[str, str]]) -> Optional[Customer]:
        """
        Resolve customer identity based on provided identifiers
        
        Args:
            identifiers: List of dicts with 'type' and 'value' keys
            
        Returns:
            Customer instance if found, None otherwise
        """
        if not identifiers:
            return None
        
        # Try exact matches first
        for identifier in identifiers:
            customer = self._find_by_exact_match(
                identifier['type'], 
                identifier['value']
            )
            if customer:
                return customer
        
        # Try fuzzy matching for email and phone
        for identifier in identifiers:
            if identifier['type'] in ['email', 'phone']:
                customer = self._find_by_fuzzy_match(
                    identifier['type'], 
                    identifier['value']
                )
                if customer:
                    return customer
        
        return None
    
    def create_customer(self, external_id: str, identifiers: List[Dict[str, str]], 
                       metadata: Optional[Dict[str, Any]] = None) -> Customer:
        """
        Create a new customer with identifiers
        
        Args:
            external_id: External customer ID
            identifiers: List of identifier dicts
            metadata: Optional customer metadata
            
        Returns:
            Created Customer instance
        """
        if metadata is None:
            metadata = {}
        
        with transaction.atomic():
            # Check if customer already exists
            existing_customer = self.resolve_identity(identifiers)
            if existing_customer:
                return existing_customer
            
            # Create new customer
            customer = Customer.objects.create(
                tenant=self.tenant,
                external_id=external_id,
                metadata=metadata
            )
            
            # Add identifiers
            for identifier in identifiers:
                self._create_identifier(
                    customer, 
                    identifier['type'], 
                    identifier['value'],
                    identifier.get('verified', False)
                )
            
            return customer
    
    def link_identifier(self, customer: Customer, identifier_type: str, 
                       identifier_value: str, verified: bool = False) -> CustomerIdentifier:
        """
        Link a new identifier to an existing customer
        
        Args:
            customer: Customer to link identifier to
            identifier_type: Type of identifier
            identifier_value: Value of identifier
            verified: Whether identifier is verified
            
        Returns:
            Created CustomerIdentifier instance
        """
        # Check for duplicates with fuzzy matching
        if identifier_type in ['email', 'phone']:
            existing = self._find_similar_identifier(identifier_type, identifier_value)
            if existing and existing.customer != customer:
                # Potential duplicate - could trigger merge workflow
                pass
        
        return self._create_identifier(customer, identifier_type, identifier_value, verified)
    
    def _find_by_exact_match(self, identifier_type: str, identifier_value: str) -> Optional[Customer]:
        """Find customer by exact identifier match"""
        try:
            identifier = CustomerIdentifier.objects.select_related('customer').get(
                customer__tenant=self.tenant,
                identifier_type=identifier_type,
                identifier_value=identifier_value
            )
            return identifier.customer
        except CustomerIdentifier.DoesNotExist:
            return None
    
    def _find_by_fuzzy_match(self, identifier_type: str, identifier_value: str) -> Optional[Customer]:
        """Find customer using fuzzy matching for similar identifiers"""
        # Get all identifiers of the same type for this tenant
        identifiers = CustomerIdentifier.objects.filter(
            customer__tenant=self.tenant,
            identifier_type=identifier_type
        ).select_related('customer')
        
        # Normalize the input value
        normalized_input = self._normalize_identifier(identifier_type, identifier_value)
        
        for identifier in identifiers:
            normalized_existing = self._normalize_identifier(
                identifier_type, 
                identifier.identifier_value
            )
            
            # Calculate similarity
            similarity = difflib.SequenceMatcher(
                None, 
                normalized_input, 
                normalized_existing
            ).ratio()
            
            if similarity >= self.fuzzy_threshold:
                return identifier.customer
        
        return None
    
    def _find_similar_identifier(self, identifier_type: str, 
                               identifier_value: str) -> Optional[CustomerIdentifier]:
        """Find similar identifier using fuzzy matching"""
        identifiers = CustomerIdentifier.objects.filter(
            customer__tenant=self.tenant,
            identifier_type=identifier_type
        )
        
        normalized_input = self._normalize_identifier(identifier_type, identifier_value)
        
        for identifier in identifiers:
            normalized_existing = self._normalize_identifier(
                identifier_type, 
                identifier.identifier_value
            )
            
            similarity = difflib.SequenceMatcher(
                None, 
                normalized_input, 
                normalized_existing
            ).ratio()
            
            if similarity >= self.fuzzy_threshold:
                return identifier
        
        return None
    
    def _create_identifier(self, customer: Customer, identifier_type: str, 
                          identifier_value: str, verified: bool = False) -> CustomerIdentifier:
        """Create a customer identifier"""
        return CustomerIdentifier.objects.create(
            customer=customer,
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            verified=verified
        )
    
    def _normalize_identifier(self, identifier_type: str, identifier_value: str) -> str:
        """Normalize identifier value for comparison"""
        value = identifier_value.lower().strip()
        
        if identifier_type == 'email':
            # Remove dots from Gmail addresses (gmail treats them as same)
            if '@gmail.com' in value:
                local, domain = value.split('@')
                local = local.replace('.', '')
                value = f"{local}@{domain}"
        
        elif identifier_type == 'phone':
            # Remove all non-digit characters
            value = ''.join(filter(str.isdigit, value))
            # Remove country code if present (assuming US +1)
            if value.startswith('1') and len(value) == 11:
                value = value[1:]
        
        return value
    
    def get_customer_identifiers(self, customer: Customer) -> List[CustomerIdentifier]:
        """Get all identifiers for a customer"""
        return list(customer.identifiers.all())
    
    def merge_customers(self, primary_customer: Customer, 
                       duplicate_customer: Customer) -> Customer:
        """
        Merge duplicate customer records
        
        Args:
            primary_customer: Customer to keep
            duplicate_customer: Customer to merge and delete
            
        Returns:
            Primary customer with merged data
        """
        with transaction.atomic():
            # Move all identifiers to primary customer
            CustomerIdentifier.objects.filter(
                customer=duplicate_customer
            ).update(customer=primary_customer)
            
            # Move all conversations to primary customer
            duplicate_customer.conversations.update(customer=primary_customer)
            
            # Merge metadata
            merged_metadata = {**duplicate_customer.metadata, **primary_customer.metadata}
            primary_customer.metadata = merged_metadata
            primary_customer.save()
            
            # Delete duplicate customer
            duplicate_customer.delete()
            
            return primary_customer
