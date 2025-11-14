from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from utils.database import get_db_connection
from utils.security import VillainSecurity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page matching Figma design"""
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user and VillainSecurity.check_password(password, user['password_hash']):
                # Login successful
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['role'] = user['role']
                session['name'] = user['name']
                
                flash('Login successful!', 'success')
                
                # Redirect based on role
                if user['role'] == 'customer':
                    return redirect(url_for('customer.dashboard'))
                elif user['role'] == 'restaurant':
                    return redirect(url_for('restaurant.dashboard'))
                elif user['role'] == 'admin':
                    return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid email or password!', 'error')
            
            cursor.close()
            conn.close()
        else:
            flash('Database connection error!', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page matching Figma design"""
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'customer') or 'customer'
        
        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/register.html')
        
        # Validate email
        if not VillainSecurity.validate_email(email):
            flash('Please enter a valid email address!', 'error')
            return render_template('auth/register.html')
        
        # Validate password strength
        is_strong, message = VillainSecurity.validate_password_strength(password)
        if not is_strong:
            flash(message, 'error')
            return render_template('auth/register.html')
        
        # Hash password
        hashed_password = VillainSecurity.hash_password(password)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO users (email, password_hash, name, phone, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (email, hashed_password, name, phone, role))
                
                conn.commit()
                new_user_id = cursor.lastrowid

                session['user_id'] = new_user_id
                session['email'] = email
                session['role'] = role
                session['name'] = name

                flash('Registration successful! Welcome to Villain Food.', 'success')
                if role == 'customer':
                    return redirect(url_for('customer.dashboard'))
                elif role == 'restaurant':
                    return redirect(url_for('restaurant.dashboard'))
                else:
                    return redirect(url_for('admin.dashboard'))
                
            except Exception as e:
                if 'UNIQUE constraint failed: users.email' in str(e):
                    flash('Email already exists!', 'error')
                else:
                    flash(f'Registration error: {str(e)}', 'error')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database connection error!', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))