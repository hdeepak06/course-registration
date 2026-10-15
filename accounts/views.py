from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import StudentRegistrationForm, StudentLoginForm

def register_view(request):
    """Handles student account registration with server-side validation."""
    if request.user.is_authenticated:
        return redirect('courses:index')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! Please log in with your credentials.")
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = StudentRegistrationForm()

    return render(request, 'register.html', {'form': form})

def login_view(request):
    """Authenticates student or administrator with secure session handling."""
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile') and request.user.student_profile.is_admin:
            return redirect('courses:admin_dashboard')
        return redirect('courses:my_courses')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']

            # Lookup username by email
            user_obj = User.objects.filter(email__iexact=email).first()
            username = user_obj.username if user_obj else email

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                full_name = user.get_full_name() or user.username
                messages.success(request, f"Welcome back, {full_name}!")

                if next_url and next_url.startswith('/'):
                    return redirect(next_url)

                if hasattr(user, 'student_profile') and user.student_profile.is_admin:
                    return redirect('courses:admin_dashboard')
                return redirect('courses:my_courses')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please correct the errors in the login form.")
    else:
        form = StudentLoginForm()

    return render(request, 'login.html', {'form': form, 'next': next_url})

def logout_view(request):
    """Terminates active session."""
    logout(request)
    messages.info(request, "You have been securely logged out.")
    return redirect('courses:index')
