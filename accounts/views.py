from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import (
    AdminLoginForm, ServiceRegistrationForm, EmployeeRegistrationForm,
    UserLoginForm, AdminUserCreateForm, AdminUserEditForm
)
from .models import User

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'

# Landing Page
def landing_view(request):
    return render(request, "accounts/landing.html")

# Admin Login
def admin_login_view(request):
    if request.method == "POST":
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.user_type == 'admin':
                login(request, user)
                messages.success(request, f"Welcome Admin {username}!")
                return redirect("accounts:admin_users")
            else:
                messages.error(request, "Invalid admin credentials or insufficient permissions.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AdminLoginForm()
    return render(request, "accounts/admin_login.html", {"form": form})

# Admin User Management
@login_required
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_users_view(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, "accounts/admin_users.html", {"users": users})

@login_required
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_user_create_view(request):
    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("accounts:admin_users")
        else:
            messages.error(request, "Error creating user. Please check the form.")
    else:
        form = AdminUserCreateForm()
    return render(request, "accounts/admin_user_form.html", {"form": form, "action": "Create"})

@login_required
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_user_edit_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("accounts:admin_users")
        else:
            messages.error(request, "Error updating user. Please check the form.")
    else:
        form = AdminUserEditForm(instance=user_obj)
    return render(request, "accounts/admin_user_form.html", {"form": form, "action": "Edit", "user_obj": user_obj})

@login_required
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_user_delete_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user_obj.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("accounts:admin_users")
    return render(request, "accounts/admin_user_delete.html", {"user_obj": user_obj})

# Service Registration & Login
def service_register_view(request):
    if request.method == "POST":
        form = ServiceRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Service registration successful!")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Registration failed. Please check the form.")
    else:
        form = ServiceRegistrationForm()
    return render(request, "accounts/service_register.html", {"form": form})

def service_login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.user_type == 'service':
                login(request, user)
                messages.success(request, f"Welcome {username}!")
                return redirect("dashboard:index")
            else:
                messages.error(request, "Invalid service credentials.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, "accounts/service_login.html", {"form": form})

# Employee Registration & Login
def employee_register_view(request):
    if request.method == "POST":
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Employee registration successful!")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Registration failed. Please check the form.")
    else:
        form = EmployeeRegistrationForm()
    return render(request, "accounts/employee_register.html", {"form": form})

def employee_login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.user_type == 'employee':
                login(request, user)
                messages.success(request, f"Welcome {username}!")
                return redirect("dashboard:index")
            else:
                messages.error(request, "Invalid employee credentials.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, "accounts/employee_login.html", {"form": form})

# Legacy views (kept for compatibility)
def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("dashboard:index")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"register_form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("dashboard:index")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"login_form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("accounts:landing")
