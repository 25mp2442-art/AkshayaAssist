from django import forms
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'annual_income', 'ration_card_type', 'category', 'occupation']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your age'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual Income in ₹'}),
            'ration_card_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Farmer, Student, Business'}),
        }