"""Context Handoff Management Service for channel transitions"""

import json
from typing import Dict, Any, Optional
from django.db import transaction
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from contexts.models import Conversation, Handoff, Customer, Tenant
from contexts.services.conversation_manager import ConversationManager


class ContextHandoffManager:
    """Service for managing context handoffs between channels"""
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.conversation_manager = ConversationManager(tenant)
    
    def prepare_handoff(self, source_conversation: Conversation, target_channel: str, 
                       handoff_reason: str, handoff_type: str = 'transfer') -> Dict[str, Any]:
        """Prepare handoff package with complete context"""
        history = self.conversation_manager.get_conversation_history(source_conversation)
        customer = source_conversation.customer
        
        context_package = {
            'customer': {
                'id': str(customer.id),
                'external_id': customer.external_id,
                'identifiers': [
                    {
                        'type': identifier.identifier_type,
                        'value': identifier.identifier_value,
                        'verified': identifier.verified
                    }
                    for identifier in customer.identifiers.all()
                ],
                'metadata': customer.metadata
            },
            'conversation_history': [
                {
                    'id': msg['id'],
                    'sender_type': msg['sender_type'],
                    'sender_id': msg['sender_id'],
                    'content': msg['content'],
                    'content_type': msg['content_type'],
                    'timestamp': msg['timestamp'].isoformat() if hasattr(msg['timestamp'], 'isoformat') else str(msg['timestamp']),
                    'metadata': msg['metadata']
                }
                for msg in history['messages']
            ],
            'handoff_info': {
                'reason': handoff_reason,
                'type': handoff_type,
                'source_channel': source_conversation.channel,
                'target_channel': target_channel,
                'initiated_at': timezone.now().isoformat()
            }
        }
        
        return context_package
    
    def execute_handoff(self, source_conversation: Conversation, target_channel: str,
                       handoff_reason: str, handoff_type: str = 'transfer',
                       target_metadata: Optional[Dict[str, Any]] = None) -> Handoff:
        """Execute handoff and create new conversation in target channel"""
        with transaction.atomic():
            context_package = self.prepare_handoff(
                source_conversation, target_channel, handoff_reason, handoff_type
            )
            
            customer_identifiers = context_package['customer']['identifiers']
            target_conversation = self.conversation_manager.create_conversation(
                customer_identifiers=customer_identifiers,
                channel=target_channel,
                metadata=target_metadata or {}
            )
            
            handoff = Handoff.objects.create(
                source_conversation=source_conversation,
                target_conversation=target_conversation,
                source_channel=source_conversation.channel,
                target_channel=target_channel,
                handoff_reason=handoff_reason,
                handoff_type=handoff_type,
                status='in_progress',
                context_package=context_package
            )
            
            self.conversation_manager.add_message(
                conversation=target_conversation,
                sender_type='system',
                sender_id='handoff_manager',
                content=f'Conversation transferred from {source_conversation.channel}. Reason: {handoff_reason}',
                content_type='text',
                metadata={'handoff_id': str(handoff.id)}
            )
            
            self.conversation_manager.update_conversation_status(
                source_conversation, 'transferred'
            )
            
            handoff.status = 'completed'
            handoff.completed_at = timezone.now()
            handoff.save()
            
            return handoff
