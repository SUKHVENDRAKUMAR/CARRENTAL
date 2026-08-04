from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CarProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Add form-control class to all fields
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f"Enter {field.label}"

class CarProfileForm(forms.ModelForm):
    class Meta:
        model = CarProfile
        fields = ['car_name', 'car_image', 'car_details', 'phone_number', 'whatsapp_number']
        widgets = {
            'car_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tesla Model 3 / BMW M4'}),
            'car_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'car_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter specifications, transmission, fuel, rent per day, etc.'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +1234567890'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +1234567890'}),
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )


class PasswordResetVerifyForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center fs-4 fw-bold',
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'off',
            'style': 'letter-spacing: 0.5rem;'
        })
    )


class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

