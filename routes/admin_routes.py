from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from utils.database import get_db_connection
from utils.security import admin_required
from utils.blockchain import VillainBlockchain

admin_bp = Blueprint('admin', __name__)
blockchain = VillainBlockchain()

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as total_restaurants FROM restaurants")
        total_restaurants = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
        total_orders = cursor.fetchone()
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status = 'delivered'")
        total_revenue = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users['total_users'],
                             total_restaurants=total_restaurants['total_restaurants'],
                             total_orders=total_orders['total_orders'],
                             total_revenue=total_revenue['total_revenue'])
    else:
        flash('Database connection error!', 'error')
        return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@admin_required
def user_management():
    """User management"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/user_management.html', users=users)
    else:
        flash('Database connection error!', 'error')
        return render_template('admin/user_management.html')

@admin_bp.route('/restaurants')
@admin_required
def restaurant_management():
    """Restaurant management"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.*, u.name as owner_name 
            FROM restaurants r 
            JOIN users u ON r.owner_id = u.id 
            ORDER BY r.created_at DESC
        """)
        restaurants = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/restaurant_management.html', restaurants=restaurants)
    else:
        flash('Database connection error!', 'error')
        return render_template('admin/restaurant_management.html')

@admin_bp.route('/security')
@admin_required
def security_config():
    """Security configuration"""
    return redirect(url_for('security.security_configuration'))

@admin_bp.route('/blockchain/verify')
@admin_required
def blockchain_verify():
    """Blockchain integrity verification"""
    integrity, message = blockchain.verify_blockchain_integrity()
    
    return render_template('admin/blockchain_verify.html',
                         integrity=integrity,
                         message=message)

@admin_bp.route('/ai-dashboard')
@admin_required
def ai_dashboard():
    """AI analytics dashboard"""
    return render_template('admin/ai_dashboard.html')

@admin_bp.route('/menu-management')
@admin_required
def menu_management():
    """Admin menu management - can manage menus for all restaurants"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Get all restaurants
        cursor.execute("SELECT * FROM restaurants ORDER BY name")
        restaurants = cursor.fetchall()
        
        # Get restaurant_id from query params if provided
        restaurant_id = request.args.get('restaurant_id', type=int)
        menu_items = []
        selected_restaurant = None
        
        if restaurant_id:
            cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
            selected_restaurant = cursor.fetchone()
            
            if selected_restaurant:
                cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ?", (restaurant_id,))
                menu_items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin/menu_management.html',
                             restaurants=restaurants,
                             selected_restaurant=selected_restaurant,
                             menu_items=menu_items)
    else:
        flash('Database connection error!', 'error')
        return render_template('admin/menu_management.html')