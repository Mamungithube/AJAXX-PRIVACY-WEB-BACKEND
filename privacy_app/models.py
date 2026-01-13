from django.db import models

class OpteryScanHistory(models.Model):
    member_uuid = models.CharField(max_length=255, db_index=True)  # Index added
    email = models.EmailField(max_length=255, db_index=True)  # Index added
    scan_id = models.CharField(max_length=255, db_index=True)  # Index added
    raw_scan_data = models.JSONField()      
    raw_screenshot_data = models.JSONField() 
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index added

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['member_uuid', 'email']),
            models.Index(fields=['email', 'created_at']),
        ]

    def __str__(self):
        return f"{self.email} - {self.scan_id}"


class OpteryMember(models.Model):
    uuid = models.UUIDField(unique=True, db_index=True, blank=True, null=True)
    email = models.EmailField(db_index=True)  # Index added
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=2, default='US')
    state = models.CharField(max_length=100, blank=True, null=True)
    birthday_day = models.IntegerField(blank=True, null=True)
    birthday_month = models.IntegerField(blank=True, null=True)
    birthday_year = models.IntegerField(blank=True, null=True)
    plan = models.CharField(max_length=50)
    postpone_scan = models.IntegerField(default=45)
    group_tag = models.CharField(max_length=100, blank=True, null=True, default='null')
    address_line1 = models.TextField(blank=True, null=True)
    address_line2 = models.TextField(blank=True, null=True)
    zipcode = models.CharField(max_length=20, blank=True, null=True)
    
    # Response details
    optery_response = models.JSONField(blank=True, null=True)
    status_code = models.IntegerField()
    is_success = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'optery_members'
        verbose_name = 'Optery Member'
        verbose_name_plural = 'Optery Members'
        indexes = [
            models.Index(fields=['email', 'created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"