from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import random
import time
from .models import CarProfile
from .forms import UserRegistrationForm, CarProfileForm, PasswordResetRequestForm, PasswordResetVerifyForm, PasswordResetConfirmForm

def home_view(request):
    # Fetch all user car profiles to display on the home page
    car_profiles = CarProfile.objects.all().order_by('-created_at')
    return render(request, 'rentals/home.html', {'car_profiles': car_profiles})

def about_view(request):
    return render(request, 'rentals/about.html')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Construct and send the email using configured Gmail SMTP
        email_subject = f"ApexDrive Support Inquiry: {subject}"
        email_body = f"You have received a new inquiry from the contact form.\n\n" \
                     f"Sender Name: {name}\n" \
                     f"Sender Email: {email}\n" \
                     f"Subject: {subject}\n\n" \
                     f"Message:\n{message}"
        
        try:
            recipient = getattr(settings, 'EMAIL_HOST_USER', '') or settings.DEFAULT_FROM_EMAIL
            email_msg = EmailMessage(
                subject=email_subject,
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
                reply_to=[email],
            )
            email_msg.send(fail_silently=False)
            messages.success(request, f"Thank you, {name}! Your message has been sent successfully. We will get back to you soon.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, "Unable to send your message at the moment. Please try again later.")
            
        return redirect('contact')
    return render(request, 'rentals/contact.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, 'rentals/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'rentals/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def profile_view(request):
    # Fetch all cars listed by this user
    profiles = request.user.car_profiles.all().order_by('-created_at')
    return render(request, 'rentals/profile.html', {'profiles': profiles})

@login_required
def add_car_view(request):
    if request.method == 'POST':
        form = CarProfileForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.user = request.user
            car.save()
            messages.success(request, f"Your car '{car.car_name}' has been listed successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Failed to list car. Please verify details.")
    else:
        form = CarProfileForm()
    
    return render(request, 'rentals/car_form.html', {'form': form, 'title': 'List a New Car', 'button_text': 'Create Listing'})

@login_required
def edit_car_view(request, car_id):
    from django.shortcuts import get_object_or_404
    car = get_object_or_404(CarProfile, id=car_id, user=request.user)
    
    if request.method == 'POST':
        form = CarProfileForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, f"Your car '{car.car_name}' details have been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Failed to update car details. Please verify your entries.")
    else:
        form = CarProfileForm(instance=car)
        
    return render(request, 'rentals/car_form.html', {'form': form, 'title': f'Update {car.car_name}', 'button_text': 'Save Changes', 'car': car})

@login_required
@require_POST
def delete_car_view(request, car_id):
    from django.shortcuts import get_object_or_404
    car = get_object_or_404(CarProfile, id=car_id, user=request.user)
    car_name = car.car_name
    car.delete()
    messages.success(request, f"Your car '{car_name}' listing has been deleted successfully.")
    return redirect('profile')


def password_reset_request_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email)
            if users.exists():
                # Generate 6 digit OTP
                otp = f"{random.randint(100000, 999999)}"
                
                # Send email
                subject = "ApexDrive - Password Reset OTP"
                message = f"Hello,\n\nYour OTP to reset your password is: {otp}\n\nThis OTP is valid for 10 minutes.\n\nThank you,\nApexDrive Team"
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    # Store details in session
                    request.session['reset_email'] = email
                    request.session['reset_otp'] = otp
                    request.session['reset_otp_time'] = time.time()
                    request.session['reset_otp_verified'] = False
                    
                    messages.success(request, f"A 6-digit OTP has been sent to {email}. Please verify below.")
                    return redirect('password_reset_verify')
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f"Failed to send email: {e}")
            else:
                messages.error(request, "No user is registered with this email address.")
    else:
        form = PasswordResetRequestForm()
    return render(request, 'rentals/password_reset_request.html', {'form': form})


def password_reset_verify_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    email = request.session.get('reset_email')
    otp = request.session.get('reset_otp')
    otp_time = request.session.get('reset_otp_time')

    if not email or not otp or not otp_time:
        messages.error(request, "Session expired or invalid access. Please start again.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetVerifyForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            # Check expiry (10 minutes = 600 seconds)
            if time.time() - otp_time > 600:
                # Clear session
                request.session.pop('reset_email', None)
                request.session.pop('reset_otp', None)
                request.session.pop('reset_otp_time', None)
                request.session.pop('reset_otp_verified', None)
                messages.error(request, "The OTP has expired. Please request a new one.")
                return redirect('password_reset_request')

            if entered_otp == otp:
                request.session['reset_otp_verified'] = True
                messages.success(request, "OTP verified successfully. Please enter your new password.")
                return redirect('password_reset_confirm')
            else:
                messages.error(request, "Invalid OTP. Please check and try again.")
    else:
        form = PasswordResetVerifyForm()
    return render(request, 'rentals/password_reset_verify.html', {'form': form, 'email': email})


def password_reset_confirm_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    email = request.session.get('reset_email')
    verified = request.session.get('reset_otp_verified')

    if not email or not verified:
        messages.error(request, "Unauthorized access. Please verify your OTP first.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['password']
            users = User.objects.filter(email=email)
            for user in users:
                user.set_password(new_password)
                user.save()
            
            # Clear session
            request.session.pop('reset_email', None)
            request.session.pop('reset_otp', None)
            request.session.pop('reset_otp_time', None)
            request.session.pop('reset_otp_verified', None)

            messages.success(request, "Your password has been reset successfully! You can now log in.")
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'rentals/password_reset_confirm.html', {'form': form})


