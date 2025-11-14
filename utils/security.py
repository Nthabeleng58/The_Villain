from functools import wraps
from flask import session, redirect, url_for, flash
import bcrypt
import re

class VillainSecurity:
    # Role-Based Access Control Permissions
    ROLE_PERMISSIONS = {
        'customer': [
            'browse_restaurants',
            'place_orders', 
            'view_own_orders',
            'write_reviews',
            'manage_cart',
            'view_own_profile'
        ],
        'restaurant': [
            'manage_restaurant',
            'view_restaurant_orders',
            'update_order_status',
            'manage_menu',
            'view_sales_reports'
        ],
        'delivery': [
            'view_assigned_orders',
            'update_delivery_status',
            'view_delivery_history'
        ],
        'admin': [
            'manage_all_users',
            'view_all_orders',
            'manage_restaurants',
            'view_system_analytics',
            'configure_system',
            'verify_blockchain'
        ]
    }
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def check_password(password, hashed):
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        return True, "Password is strong"
    
    @staticmethod
    def has_permission(required_permission):
        """Decorator to check user permissions"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    flash('Please login to access this page.', 'error')
                    return redirect(url_for('auth.login'))
                
                user_role = session.get('role', 'customer')
                user_permissions = VillainSecurity.ROLE_PERMISSIONS.get(user_role, [])
                
                if required_permission not in user_permissions:
                    flash('Access denied. Insufficient permissions.', 'error')
                    return redirect(url_for('customer.dashboard'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Security middleware for specific roles
def admin_required(f):
    return VillainSecurity.has_permission('manage_all_users')(f)

def restaurant_owner_required(f):
    return VillainSecurity.has_permission('manage_restaurant')(f)

def customer_required(f):
    return VillainSecurity.has_permission('place_orders')(f)