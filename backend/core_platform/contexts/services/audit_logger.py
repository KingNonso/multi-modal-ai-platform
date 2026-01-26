"""Audit Logging Service for compliance and tracking"""

from typing import Dict, Any, Optional
from django.utils import timezone
from contexts.models import AuditLog, Tenant


class AuditLogger:
    """Service for comprehensive audit logging"""
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
    
    def log_data_access(self, actor_type: str, actor_id: str, resource_type: str,
                       resource_id: str, action: str, ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None, request_data: Optional[Dict[str, Any]] = None) -> AuditLog:
        """Log data access operations"""
        return self._create_audit_log(
            event_type='data_access',
            actor_type=actor_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data or {}
        )
    
    def log_data_modification(self, actor_type: str, actor_id: str, resource_type: str,
                            resource_id: str, action: str, before_data: Optional[Dict[str, Any]] = None,
                            after_data: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None) -> AuditLog:
        """Log data modification operations with before/after values"""
        request_data = {}
        if before_data:
            request_data['before'] = before_data
        if after_data:
            request_data['after'] = after_data
        
        return self._create_audit_log(
            event_type='data_modification',
            actor_type=actor_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data
        )
    
    def log_api_call(self, actor_type: str, actor_id: str, action: str,
                    request_data: Optional[Dict[str, Any]] = None,
                    response_data: Optional[Dict[str, Any]] = None,
                    ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuditLog:
        """Log external API interactions"""
        return self._create_audit_log(
            event_type='api_call',
            actor_type=actor_type,
            actor_id=actor_id,
            resource_type='api',
            resource_id='external',
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data or {},
            response_data=response_data or {}
        )
    
    def _create_audit_log(self, event_type: str, actor_type: str, actor_id: str,
                         resource_type: str, resource_id: str, action: str,
                         ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                         request_data: Optional[Dict[str, Any]] = None,
                         response_data: Optional[Dict[str, Any]] = None) -> AuditLog:
        """Create audit log entry"""
        return AuditLog.objects.create(
            tenant=self.tenant,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data or {},
            response_data=response_data or {}
        )
