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

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ration_card_type = models.CharField(max_length=10, choices=RATION_CHOICES, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Scheme(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    max_income_limit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum annual income allowed")
    allowed_ration_card = models.CharField(max_length=10, choices=[('BPL', 'BPL Only'), ('ALL', 'All (APL & BPL)')], default='ALL')
    allowed_category = models.CharField(max_length=20, choices=[('ALL', 'All Categories'), ('OBC', 'OBC'), ('SC', 'SC'), ('ST', 'ST'), ('General', 'General')], default='ALL')
    benefits = models.TextField(help_text="What benefits the user gets")

    def __str__(self):
        return self.title

class Application(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE)
    applied_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.scheme.title}"
        