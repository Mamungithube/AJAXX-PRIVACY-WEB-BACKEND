from django.db import models

class OpteryScanHistory(models.Model):
    member_uuid = models.CharField(max_length=255)
    scan_id = models.CharField(max_length=255)
    raw_scan_data = models.JSONField()        # scan response
    raw_screenshot_data = models.JSONField()  # screenshot response
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member_uuid} - {self.scan_id}"
