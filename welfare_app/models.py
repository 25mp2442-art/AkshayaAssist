import random
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
    ]
    
    RATION_CHOICES = [
        ('BPL', 'BPL (Yellow/Pink Card)'),
        ('APL', 'APL (Blue/White Card)'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ration_card_type = models.CharField(max_length=10, choices=RATION_CHOICES, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Scheme(models.Model):
    GENDER_CHOICES = [
        ('ALL', 'ALL (Everyone)'),
        ('Female', 'Female Only'),
        ('Male', 'Male Only'),
    ]

    OCCUPATION_CHOICES = [
        ('ALL', 'ALL (Any Occupation)'),
        ('Farmer', 'Farmer'),
        ('Teacher', 'Teacher'),
        ('Student', 'Student'),
    ]

    RATION_CHOICES = [
        ('ALL', 'ALL (APL & BPL)'),
        ('APL', 'APL Only'),
        ('BPL', 'BPL Only'),
    ]

    CATEGORY_CHOICES = [
        ('ALL', 'ALL Categories'),
        ('General', 'General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    min_age = models.IntegerField(default=0)
    max_income = models.IntegerField(default=100000)
    
    # ഡ്രോപ്പ് ഡൗൺ ഓപ്ഷനുകൾ
    allowed_ration_cards = models.CharField(max_length=20, choices=RATION_CHOICES, default='ALL')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='ALL')
    allowed_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='ALL')
    required_occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES, default='ALL')
    
    required_documents = models.CharField(max_length=300, default="Aadhaar Card, Income Certificate")

    # ഓരോ ഗവൺമെന്റ് പദ്ധതിക്കും ചോദിക്കേണ്ട പ്രത്യേക കാര്യങ്ങൾ
    # ഉദാഹരണത്തിന്: "Land Details, Survey Number" അല്ലെങ്കിൽ "College Name, Course, Marks Percentage"
    extra_fields = models.CharField(
        max_length=500, 
        blank=True, 
        default="", 
        help_text="അഡീഷണൽ ചോദ്യങ്ങൾ കോമ (,) ഇട്ട് എഴുതുക."
    )
    def __str__(self):
        return self.title

import uuid
from django.db import models
from django.contrib.auth.models import User

class Application(models.Model):
    STATUS_CHOICES = [
        ('Submitted', 'Submitted to Akshaya'),
        ('Under Verification', 'Under Verification'),
        ('Forwarded to Govt', 'Forwarded to Govt Dept'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE)
    token_number = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Submitted')
    
    phone_number = models.CharField(max_length=15, default="")
    document = models.FileField(upload_to='application_docs/', null=True, blank=True)
    
    # സ്റ്റാഫ് പൂരിപ്പിക്കുന്ന അഡീഷണൽ ഡാറ്റ സേവ് ചെയ്യാൻ
    form_data = models.JSONField(default=dict, blank=True)
    staff_remarks = models.TextField(blank=True, default="Documents submitted. Awaiting verification.")

    def save(self, *args, **kwargs):
        if not self.token_number:
            self.token_number = f"AKS-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.token_number} - {self.user.username}"