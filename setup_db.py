"""
Quick setup script to reset database and create admin user
Run this with: python setup_db.py
"""

import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

def create_admin_user():
    """Create the initial admin user"""
    print("\n=== Creating Admin User ===")
    
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email (default: admin@ebikesystem.com): ").strip() or "admin@ebikesystem.com"
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"❌ User '{username}' already exists!")
        return
    
    password = input("Enter admin password (default: admin123): ").strip() or "admin123"
    
    try:
        admin = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        print(f"\n✅ Admin user created successfully!")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   User Type: {admin.user_type}")
        print(f"\n🔗 Login at: http://localhost:8000/accounts/admin/login/")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)

def create_sample_users():
    """Create sample service and employee users for testing"""
    print("\n=== Creating Sample Users ===")
    
    create_samples = input("Create sample users for testing? (y/n): ").strip().lower()
    if create_samples != 'y':
        return
    
    try:
        # Sample Service User
        if not User.objects.filter(username='service1').exists():
            service_user = User.objects.create_user(
                username='service1',
                email='service1@ebikesystem.com',
                password='service123',
                user_type='service',
                phone='1234567890',
                is_active=True
            )
            print(f"✅ Service user created: {service_user.username}")
        
        # Sample Employee User
        if not User.objects.filter(username='employee1').exists():
            employee_user = User.objects.create_user(
                username='employee1',
                email='employee1@ebikesystem.com',
                password='employee123',
                user_type='employee',
                phone='0987654321',
                is_active=True
            )
            print(f"✅ Employee user created: {employee_user.username}")
        
        print("\n📝 Sample Users Created:")
        print("   Service - Username: service1, Password: service123")
        print("   Employee - Username: employee1, Password: employee123")
        
    except Exception as e:
        print(f"❌ Error creating sample users: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("E-Bike System - Database Setup")
    print("=" * 50)
    
    print("\n⚠️  IMPORTANT: Make sure you have:")
    print("   1. Dropped and recreated the database")
    print("   2. Run 'python manage.py migrate'")
    print("\n   If not, press Ctrl+C to cancel and run:")
    print("   - DROP DATABASE ebike_system; CREATE DATABASE ebike_system;")
    print("   - python manage.py migrate")
    
    proceed = input("\nReady to proceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Setup cancelled.")
        sys.exit(0)
    
    create_admin_user()
    create_sample_users()
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("=" * 50)
    print("\n🚀 Next Steps:")
    print("   1. Start the server: python manage.py runserver")
    print("   2. Access admin login: http://localhost:8000/accounts/admin/login/")
    print("   3. Access service login: http://localhost:8000/accounts/service/login/")
    print("   4. Access employee login: http://localhost:8000/accounts/employee/login/")
    print()
