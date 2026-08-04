from django.db import models
from django.contrib.auth.models import User

class CarProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='car_profiles')
    car_name = models.CharField(max_length=150, verbose_name="Car Model / Name")
    car_image = models.ImageField(upload_to='car_photos/', verbose_name="Car Image")
    car_details = models.TextField(verbose_name="Car Specifications and Rental Details")
    phone_number = models.CharField(max_length=20, verbose_name="Contact Number for Calls")
    whatsapp_number = models.CharField(max_length=20, verbose_name="WhatsApp Number")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.car_name}"

    @property
    def whatsapp_link(self):
        # Format the whatsapp number for wa.me link.
        # Strip spaces, dashes, parentheses, plus signs.
        clean_num = ''.join(c for c in self.whatsapp_number if c.isdigit())
        return f"https://wa.me/{clean_num}"

    @property
    def call_link(self):
        # Format phone number for tel: link.
        clean_num = ''.join(c for c in self.phone_number if c.isdigit() or c == '+')
        return f"tel:{clean_num}"
