import uuid
from django.db import models
from django.contrib.auth.models import User

# Choice Options
RATION_CARD_CHOICES = [
    ('AY', 'Antyodaya Anna Yojana (Yellow/Manja)'),
    ('PHH', 'Priority Household (Pink)'),
    ('NPS', 'Non-Priority State (Blue)'),
    ('NPNS', 'Non-Priority Non-State (White)'),
    ('ALL', 'All Ration Cards'),
]

CATEGORY_CHOICES = [
    ('GENERAL', 'General'),
    ('OBC', 'OBC'),
    ('SC', 'SC'),
    ('ST', 'ST'),
    ('ALL', 'All Categories'),
]

GENDER_CHOICES = [
    ('MALE', 'Male'),
    ('FEMALE', 'Female'),
    ('OTHER', 'Other'),
    ('ALL', 'All Genders'),
]

OCCUPATION_CHOICES = [
    ('FARMER', 'Farmer'),
    ('STUDENT', 'Student'),
    ('FISHERMAN', 'Fisherman'),
    ('EX_SERVICE', 'Ex-Serviceman'),
    ('UNEMPLOYED', 'Unemployed'),
    ('SELF_EMPLOYED', 'Self Employed'),
    ('OTHER', 'Other'),
    ('ALL', 'All Occupations'),
]

MARITAL_STATUS_CHOICES = [
    ('SINGLE', 'Single'),
    ('MARRIED', 'Married'),
    ('WIDOW', 'Widow/Widower'),
    ('DIVORCED', 'Divorced'),
    ('ALL', 'All Statuses'),
]

STATUS_CHOICES = [
    ('PENDING_VERIFICATION', 'Pending Akshaya Verification'),
    ('REJECTED_DOCS', 'Rejected - Reupload Required'),
    ('DOCS_APPROVED', 'Approved - Book Appointment'),
    ('TOKEN_BOOKED', 'Token Booked - Waiting in Queue'),
    ('IN_PROGRESS', 'At Counter - Processing'),
    ('FORWARDED_TO_GOVT', 'Submitted to Government Portal'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ration_card_type = models.CharField(max_length=10, choices=RATION_CARD_CHOICES, null=True, blank=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, null=True, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    
    is_differently_abled = models.BooleanField(default=False)
    disability_type = models.CharField(max_length=100, null=True, blank=True)
    disability_percentage = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Scheme(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=100)
    
    # Eligibility Criteria
    max_income = models.DecimalField(max_digits=10, decimal_places=2, default=999999)
    min_age = models.IntegerField(default=0)
    allowed_ration_cards = models.CharField(max_length=10, choices=RATION_CARD_CHOICES, default='ALL')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='ALL')
    allowed_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='ALL')
    required_occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, default='ALL')
    allowed_marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, default='ALL')
    is_for_disabled_only = models.BooleanField(default=False)

    required_documents = models.TextField(help_text="Comma separated document names (e.g., Aadhaar, Income Certificate)", blank=True)
    extra_fields = models.TextField(help_text="Comma separated custom input field names", blank=True)

    def __str__(self):
        return self.title

class Application(models.Model):
    application_id = models.CharField(max_length=12, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='applications')
    phone_number = models.CharField(max_length=15, blank=True)
    form_data = models.JSONField(default=dict, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_VERIFICATION')
    applied_date = models.DateTimeField(auto_now_add=True)
    
    # Verification & Rejection Remarks
    rejection_reason = models.TextField(blank=True, null=True)
    staff_remarks = models.TextField(blank=True, null=True)

    # Queue & Counter Booking
    appointment_date = models.DateField(null=True, blank=True)
    token_number = models.IntegerField(null=True, blank=True)

    # Final Govt Forwarding
    govt_ref_number = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.application_id:
            self.application_id = str(uuid.uuid4().hex[:10]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_id} - {self.user.username} ({self.scheme.title})"

class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='application_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_name} for {self.application.application_id}"