from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import uuid


class Tenant(models.Model):
    """Multi-tenant organization model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    subscription_tier = models.CharField(
        max_length=50,
        choices=[
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='basic'
    )
    data_residency = models.CharField(
        max_length=10,
        choices=[
            ('us', 'United States'),
            ('eu', 'European Union'),
            ('apac', 'Asia Pacific'),
        ],
        default='us'
    )
    retention_days = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(1)]
    )
    rate_limit_per_minute = models.PositiveIntegerField(
        default=1000,
        validators=[MinValueValidator(1)]
    )
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['subscription_tier']),
        ]

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Customer model with tenant isolation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='customers')
    external_id = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        unique_together = [['tenant', 'external_id']]
        indexes = [
            models.Index(fields=['tenant', 'external_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.external_id}"


class CustomerIdentifier(models.Model):
    """Customer identifiers for cross-channel identity resolution"""
    IDENTIFIER_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('account_id', 'Account ID'),
        ('user_id', 'User ID'),
        ('session_id', 'Session ID'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='identifiers')
    identifier_type = models.CharField(max_length=50, choices=IDENTIFIER_TYPES)
    identifier_value = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_identifiers'
        unique_together = [['identifier_type', 'identifier_value']]
        indexes = [
            models.Index(fields=['identifier_type', 'identifier_value']),
            models.Index(fields=['customer']),
        ]

    def __str__(self):
        return f"{self.identifier_type}: {self.identifier_value}"


class Conversation(models.Model):
    """Conversation model for tracking customer interactions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('waiting', 'Waiting'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('transferred', 'Transferred'),
    ]

    CHANNEL_CHOICES = [
        ('web', 'Web Chat'),
        ('mobile', 'Mobile App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('voice', 'Voice'),
        ('social', 'Social Media'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='conversations')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='conversations')
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'conversations'
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['tenant']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['channel']),
        ]

    def __str__(self):
        return f"Conversation {self.id} - {self.customer}"


class Message(models.Model):
    """Message model with partitioning support"""
    SENDER_TYPES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
        ('system', 'System'),
        ('bot', 'Bot'),
    ]

    CONTENT_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=50, choices=SENDER_TYPES)
    sender_id = models.CharField(max_length=255)
    content = models.TextField()
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, default='text')
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['conversation']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['sender_type']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender_type} at {self.timestamp}"


class Handoff(models.Model):
    """Handoff model for channel transitions"""
    HANDOFF_TYPES = [
        ('escalation', 'Escalation'),
        ('transfer', 'Transfer'),
        ('routing', 'Routing'),
    ]

    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='outgoing_handoffs'
    )
    target_conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='incoming_handoffs',
        null=True, 
        blank=True
    )
    source_channel = models.CharField(max_length=50)
    target_channel = models.CharField(max_length=50)
    handoff_reason = models.TextField()
    handoff_type = models.CharField(max_length=50, choices=HANDOFF_TYPES)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='initiated')
    context_package = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'handoffs'
        indexes = [
            models.Index(fields=['source_conversation']),
            models.Index(fields=['target_conversation']),
            models.Index(fields=['status']),
            models.Index(fields=['initiated_at']),
        ]

    def __str__(self):
        return f"Handoff {self.id} - {self.source_channel} to {self.target_channel}"


class AuditLog(models.Model):
    """Immutable audit log for compliance and tracking"""
    EVENT_TYPES = [
        ('data_access', 'Data Access'),
        ('data_modification', 'Data Modification'),
        ('api_call', 'API Call'),
        ('authentication', 'Authentication'),
        ('authorization', 'Authorization'),
    ]

    ACTOR_TYPES = [
        ('user', 'User'),
        ('system', 'System'),
        ('api_client', 'API Client'),
    ]

    RESOURCE_TYPES = [
        ('customer', 'Customer'),
        ('conversation', 'Conversation'),
        ('message', 'Message'),
        ('handoff', 'Handoff'),
        ('tenant', 'Tenant'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='audit_logs')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    actor_type = models.CharField(max_length=50, choices=ACTOR_TYPES)
    actor_id = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    resource_id = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'audit_log'
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['actor_type', 'actor_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['event_type']),
        ]

    def save(self, *args, **kwargs):
        # Prevent updates to audit log entries
        if self.pk is not None and self._state.adding is False:
            raise ValueError("Audit log entries cannot be modified")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of audit log entries
        raise ValueError("Audit log entries cannot be deleted")

    def __str__(self):
        return f"Audit: {self.event_type} by {self.actor_type} at {self.timestamp}"
