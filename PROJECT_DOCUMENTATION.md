# E-Bike System - Project Documentation

## Overview
This is a Django-based E-Bike Management System with role-based access control for Admin, Service, and Employee users.

## Project Structure

```
ebike_system/
├── config/                 # Project configuration
│   ├── settings.py        # Django settings (admin panel disabled)
│   ├── urls.py            # Main URL routing
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
│
├── accounts/              # User authentication & management
│   ├── models.py          # Custom User model with user_type field
│   ├── views.py           # Login, registration, and admin views
│   ├── urls.py            # Authentication URLs
│   ├── forms.py           # Custom forms for different user types
│   └── migrations/
│
├── dashboard/             # Dashboard app
├── inventory/             # Inventory management
├── approvals/             # Approval workflows
├── sales/                 # Sales tracking
├── attendance/            # Attendance management
├── services/              # Service management
├── reports/               # Reporting functionality
│
└── templates/             # HTML templates
    ├── base.html          # Base template with navigation
    └── accounts/
        ├── landing.html           # Landing page with role selection
        ├── admin_login.html       # Admin login
        ├── service_login.html     # Service login
        ├── employee_login.html    # Employee login
        ├── service_register.html  # Service registration
        └── employee_register.html # Employee registration
```

## Key Features

### 1. Landing Page
- **URL**: `/` (root)
- **Purpose**: Entry point for all users
- **Features**:
  - Three distinct portals for Admin, Service, and Employee
  - Visual card-based navigation with icons
  - Links to login and registration pages
  - Clean, minimal design

### 2. User Roles
The system supports three user types:

#### Admin
- **Login URL**: `/accounts/admin/login/`
- **Access**: User management dashboard
- **Capabilities**: Create, edit, delete users; manage all system aspects
- **No Registration**: Admins are created manually

#### Service
- **Login URL**: `/accounts/service/login/`
- **Register URL**: `/accounts/service/register/`
- **Access**: Service-related features
- **Capabilities**: Manage repairs and maintenance

#### Employee
- **Login URL**: `/accounts/employee/login/`
- **Register URL**: `/accounts/employee/register/`
- **Access**: Employee-related features
- **Capabilities**: Sales and inventory management

### 3. Custom User Model
- Located in: `accounts/models.py`
- Field: `user_type` (choices: 'admin', 'service', 'employee')
- Extends Django's AbstractUser
- Custom authentication based on user type

### 4. Admin Features (Custom, Not Django Admin Panel)
- **Django admin panel is DISABLED**
- Custom admin interface at `/accounts/admin/users/`
- Features:
  - View all users
  - Create new users with any role
  - Edit existing users
  - Delete users
  - Access restricted to admin users only

## Important Configuration Changes

### Django Admin Panel
✅ **DISABLED** - Not used in this project
- Removed from `INSTALLED_APPS` in settings.py
- URL route commented out in config/urls.py
- All admin functionality through custom views

### Database
- **Engine**: MySQL
- **Database Name**: ebike_system
- **User**: root
- **Password**: Dev@123
- **Host**: localhost
- **Port**: 3306

### Static Files
- **STATIC_URL**: `/static/`
- **STATICFILES_DIRS**: `BASE_DIR / "static"`
- **MEDIA_URL**: `/media/`
- **MEDIA_ROOT**: `BASE_DIR / "media"`

## URL Routes

### Main Routes
| URL Pattern | App | Description |
|-------------|-----|-------------|
| `/` | accounts | Landing page with role selection |
| `/dashboard/` | dashboard | Dashboard (login required) |
| `/accounts/` | accounts | Authentication routes |
| `/inventory/` | inventory | Inventory management |
| `/approvals/` | approvals | Approval workflows |
| `/sales/` | sales | Sales tracking |
| `/attendance/` | attendance | Attendance management |
| `/services/` | services | Service management |
| `/reports/` | reports | Reports |

### Account Routes
| URL | View | Name | Access |
|-----|------|------|--------|
| `/` | landing_view | accounts:landing | Public |
| `/accounts/admin/login/` | admin_login_view | accounts:admin_login | Public |
| `/accounts/admin/users/` | admin_users_view | accounts:admin_users | Admin only |
| `/accounts/admin/users/create/` | admin_user_create_view | accounts:admin_user_create | Admin only |
| `/accounts/admin/users/<id>/edit/` | admin_user_edit_view | accounts:admin_user_edit | Admin only |
| `/accounts/admin/users/<id>/delete/` | admin_user_delete_view | accounts:admin_user_delete | Admin only |
| `/accounts/service/register/` | service_register_view | accounts:service_register | Public |
| `/accounts/service/login/` | service_login_view | accounts:service_login | Public |
| `/accounts/employee/register/` | employee_register_view | accounts:employee_register | Public |
| `/accounts/employee/login/` | employee_login_view | accounts:employee_login | Public |
| `/accounts/logout/` | logout_view | accounts:logout | Authenticated |

## How It Works

### User Flow

1. **Visitor Access**
   - User visits root URL `/`
   - Landing page displays three portal options
   - User selects their role (Admin/Service/Employee)

2. **Authentication**
   - User clicks on appropriate login button
   - Redirected to role-specific login page
   - Credentials validated against user type
   - On success: redirect to dashboard
   - On failure: error message displayed

3. **Registration** (Service & Employee only)
   - Available from landing page
   - User fills registration form
   - Account created with appropriate user_type
   - Auto-login after successful registration
   - Redirect to dashboard

4. **Admin Management**
   - Admin logs in via admin portal
   - Access to user management interface
   - Can perform CRUD operations on all users
   - Protected by `@user_passes_test(is_admin)` decorator

5. **Logout**
   - Logout link in navigation bar
   - Clears session
   - Redirects to landing page

### Navigation
- **Navbar**: Shows on all pages (from base.html)
- **Brand Link**: Always returns to landing page
- **Authenticated Users**: See username and logout link
- **Unauthenticated Users**: See "Home" link to landing page

## Security Features

1. **Role-Based Access Control**
   - Each login view validates user_type
   - Admin views protected by `@user_passes_test(is_admin)`
   - Dashboard requires `@login_required`

2. **Password Validation**
   - Django's built-in password validators enabled
   - Checks for similarity, minimum length, common passwords, numeric-only

3. **CSRF Protection**
   - Enabled via middleware
   - All forms protected

## Design Principles

### Simplicity
- Minimal, lightweight UI
- No unnecessary complexity
- Clean Bootstrap-based design

### User-Centric
- Clear role separation
- Intuitive navigation
- Visual feedback via icons and colors

### Maintainability
- Modular app structure
- Reusable templates (base.html)
- Clear separation of concerns

## Development Notes

### Custom Forms
Located in `accounts/forms.py`:
- `AdminLoginForm`: Admin authentication
- `ServiceRegistrationForm`: Service user registration
- `EmployeeRegistrationForm`: Employee user registration
- `UserLoginForm`: Generic login for Service/Employee
- `AdminUserCreateForm`: Admin creates users
- `AdminUserEditForm`: Admin edits users

### Templates
All templates extend `base.html` which includes:
- Bootstrap 5.3.0 CSS/JS
- Responsive navbar
- Message display (Django messages framework)
- Consistent styling

### Middleware
Standard Django middleware stack:
- Security
- Sessions
- CSRF
- Authentication
- Messages
- Clickjacking protection

## Future Enhancements

Potential areas for expansion:
1. Password reset functionality
2. Email verification
3. Two-factor authentication
4. User profile management
5. Activity logging
6. Advanced reporting
7. API endpoints for mobile apps

## Troubleshooting

### Issue: Cannot access Django admin
**Solution**: Django admin panel is intentionally disabled. Use custom admin interface at `/accounts/admin/login/`

### Issue: Login redirects to wrong page
**Solution**: Check user_type in authentication views - each role has specific validation

### Issue: Template not found
**Solution**: Ensure `DIRS: [BASE_DIR / "templates"]` is set in settings.py TEMPLATES config

### Issue: Static files not loading
**Solution**: Run `python manage.py collectstatic` in production; in development, ensure DEBUG=True

## Running the Application

### Setup
```bash
# Install dependencies
pip install django django-filter mysqlclient

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser
# Note: You'll need to manually set user_type='admin' in database or via shell

# Run development server
python manage.py runserver
```

### Access Points
- Landing Page: http://localhost:8000/
- Admin Login: http://localhost:8000/accounts/admin/login/
- Service Login: http://localhost:8000/accounts/service/login/
- Employee Login: http://localhost:8000/accounts/employee/login/

## Contact & Support
For issues or questions about this system, refer to the development team.

---
*Last Updated: January 2026*
