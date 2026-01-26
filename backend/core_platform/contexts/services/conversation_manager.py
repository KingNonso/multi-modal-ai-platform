"""Conversation Management Service for handling customer interactions"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from contexts.models import Customer, Conversation, Message, Tenant
from contexts.services.identity_resolver import IdentityResolver


class ConversationManager:
    """
    Service for managing conversations and messages
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.identity_resolver = IdentityResolver(tenant)
    
    def create_conversation(self, customer_identifiers: List[Dict[str, str]], 
                          channel: str, metadata: Optional[Dict[str, Any]] = None) -> Conversation:
        """
        Create or retrieve active conversation for a customer
        
        Args:
            customer_identifiers: List of customer identifier dicts
            channel: Communication channel
            metadata: Optional conversation metadata
            
        Returns:
            Conversation instance (new or existing active one)
        """
        if metadata is None:
            metadata = {}
        
        with transaction.atomic():
            # Resolve customer identity
            customer = self.identity_resolver.resolve_identity(customer_identifiers)
            
            if not customer:
                # Create new customer if not found
                external_id = f"auto-{timezone.now().timestamp()}"
                customer = self.identity_resolver.create_customer(
                    external_id=external_id,
                    identifiers=customer_identifiers
                )
            
            # Check for existing active conversation on same channel
            existing_conversation = Conversation.objects.filter(
                customer=customer,
                tenant=self.tenant,
                channel=channel,
                status__in=['active', 'waiting']
            ).first()
            
            if existing_conversation:
                # Update metadata if provided
                if metadata:
                    existing_conversation.metadata.update(metadata)
                    existing_conversation.save()
                return existing_conversation
            
            # Create new conversation
            conversation = Conversation.objects.create(
                customer=customer,
                tenant=self.tenant,
                channel=channel,
                status='active',
                metadata=metadata
            )
            
            return conversation
    
    def add_message(self, conversation: Conversation, sender_type: str, 
                   sender_id: str, content: str, content_type: str = 'text',
                   metadata: Optional[Dict[str, Any]] = None) -> Message:
        """
        Add a message to a conversation with validation
        
        Args:
            conversation: Conversation to add message to
            sender_type: Type of sender (customer, agent, system, bot)
            sender_id: ID of the sender
            content: Message content
            content_type: Type of content (text, image, file, etc.)
            metadata: Optional message metadata
            
        Returns:
            Created Message instance
            
        Raises:
            ValueError: If message validation fails
        """
        if metadata is None:
            metadata = {}
        
        # Validate message content
        self._validate_message(sender_type, content, content_type)
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            content_type=content_type,
            metadata=metadata
        )
        
        # Update conversation status if needed
        if conversation.status == 'waiting' and sender_type == 'customer':
            conversation.status = 'active'
            conversation.save()
        
        return message
    
    def get_conversation_history(self, conversation: Conversation, 
                               page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """
        Get paginated conversation history
        
        Args:
            conversation: Conversation to get history for
            page: Page number (1-based)
            page_size: Number of messages per page
            
        Returns:
            Dict with messages, pagination info, and conversation details
        """
        messages = Message.objects.filter(
            conversation=conversation
        ).order_by('timestamp')
        
        paginator = Paginator(messages, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'conversation': {
                'id': str(conversation.id),
                'customer_id': str(conversation.customer.id),
                'channel': conversation.channel,
                'status': conversation.status,
                'started_at': conversation.started_at,
                'ended_at': conversation.ended_at,
                'metadata': conversation.metadata
            },
            'messages': [
                {
                    'id': str(msg.id),
                    'sender_type': msg.sender_type,
                    'sender_id': msg.sender_id,
                    'content': msg.content,
                    'content_type': msg.content_type,
                    'timestamp': msg.timestamp,
                    'metadata': msg.metadata
                }
                for msg in page_obj
            ],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_messages': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }
    
    def get_customer_conversations(self, customer: Customer, 
                                 status_filter: Optional[str] = None,
                                 channel_filter: Optional[str] = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Get all conversations for a customer with optional filtering
        
        Args:
            customer: Customer to get conversations for
            status_filter: Optional status filter
            channel_filter: Optional channel filter
            page: Page number (1-based)
            page_size: Number of conversations per page
            
        Returns:
            Dict with conversations and pagination info
        """
        conversations = Conversation.objects.filter(
            customer=customer,
            tenant=self.tenant
        ).order_by('-started_at')
        
        # Apply filters
        if status_filter:
            conversations = conversations.filter(status=status_filter)
        
        if channel_filter:
            conversations = conversations.filter(channel=channel_filter)
        
        paginator = Paginator(conversations, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'customer': {
                'id': str(customer.id),
                'external_id': customer.external_id,
                'metadata': customer.metadata
            },
            'conversations': [
                {
                    'id': str(conv.id),
                    'channel': conv.channel,
                    'status': conv.status,
                    'started_at': conv.started_at,
                    'ended_at': conv.ended_at,
                    'message_count': conv.messages.count(),
                    'metadata': conv.metadata
                }
                for conv in page_obj
            ],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_conversations': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }
    
    def update_conversation_status(self, conversation: Conversation, 
                                 new_status: str, end_conversation: bool = False) -> Conversation:
        """
        Update conversation status
        
        Args:
            conversation: Conversation to update
            new_status: New status value
            end_conversation: Whether to set ended_at timestamp
            
        Returns:
            Updated conversation
        """
        conversation.status = new_status
        
        if end_conversation and not conversation.ended_at:
            conversation.ended_at = timezone.now()
        
        conversation.save()
        return conversation
    
    def search_conversations(self, query: str, channel: Optional[str] = None,
                           status: Optional[str] = None, 
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search conversations by message content or metadata
        
        Args:
            query: Search query
            channel: Optional channel filter
            status: Optional status filter
            page: Page number
            page_size: Results per page
            
        Returns:
            Search results with pagination
        """
        # Search in messages and get related conversations
        message_conversations = Conversation.objects.filter(
            tenant=self.tenant,
            messages__content__icontains=query
        ).distinct()
        
        # Search in conversation metadata
        metadata_conversations = Conversation.objects.filter(
            tenant=self.tenant,
            metadata__icontains=query
        )
        
        # Combine results
        conversations = (message_conversations | metadata_conversations).distinct()
        
        # Apply filters
        if channel:
            conversations = conversations.filter(channel=channel)
        
        if status:
            conversations = conversations.filter(status=status)
        
        conversations = conversations.order_by('-started_at')
        
        paginator = Paginator(conversations, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            'query': query,
            'filters': {
                'channel': channel,
                'status': status
            },
            'conversations': [
                {
                    'id': str(conv.id),
                    'customer_id': str(conv.customer.id),
                    'channel': conv.channel,
                    'status': conv.status,
                    'started_at': conv.started_at,
                    'ended_at': conv.ended_at,
                    'message_count': conv.messages.count(),
                    'metadata': conv.metadata
                }
                for conv in page_obj
            ],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_results': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        }
    
    def _validate_message(self, sender_type: str, content: str, content_type: str) -> None:
        """
        Validate message data
        
        Args:
            sender_type: Type of sender
            content: Message content
            content_type: Type of content
            
        Raises:
            ValueError: If validation fails
        """
        valid_sender_types = ['customer', 'agent', 'system', 'bot']
        if sender_type not in valid_sender_types:
            raise ValueError(f"Invalid sender_type. Must be one of: {valid_sender_types}")
        
        valid_content_types = ['text', 'image', 'file', 'audio', 'video']
        if content_type not in valid_content_types:
            raise ValueError(f"Invalid content_type. Must be one of: {valid_content_types}")
        
        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")
        
        # Additional validation for different content types
        if content_type == 'text' and len(content) > 10000:
            raise ValueError("Text message too long (max 10000 characters)")
    
    def get_conversation_summary(self, conversation: Conversation) -> Dict[str, Any]:
        """
        Get conversation summary with key metrics
        
        Args:
            conversation: Conversation to summarize
            
        Returns:
            Summary dict with metrics and key info
        """
        messages = conversation.messages.all()
        
        # Calculate metrics
        total_messages = messages.count()
        customer_messages = messages.filter(sender_type='customer').count()
        agent_messages = messages.filter(sender_type='agent').count()
        system_messages = messages.filter(sender_type='system').count()
        bot_messages = messages.filter(sender_type='bot').count()
        
        # Calculate duration
        duration = None
        if conversation.ended_at:
            duration = (conversation.ended_at - conversation.started_at).total_seconds()
        
        return {
            'conversation_id': str(conversation.id),
            'customer_id': str(conversation.customer.id),
            'channel': conversation.channel,
            'status': conversation.status,
            'started_at': conversation.started_at,
            'ended_at': conversation.ended_at,
            'duration_seconds': duration,
            'message_counts': {
                'total': total_messages,
                'customer': customer_messages,
                'agent': agent_messages,
                'system': system_messages,
                'bot': bot_messages
            },
            'metadata': conversation.metadata
        }
