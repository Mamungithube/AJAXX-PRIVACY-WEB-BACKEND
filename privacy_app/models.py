from django.db import models



class add_member(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    birthday_day = models.IntegerField()
    birthday_month = models.IntegerField()
    birthday_year = models.IntegerField()
    plan = models.CharField(max_length=100, blank=True, null=True)
    postpone_scan = models.BooleanField(default=False)
    group_tag = models.CharField(max_length=100, blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=20)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"