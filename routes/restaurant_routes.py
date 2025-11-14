from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from utils.database import get_db_connection
from utils.security import restaurant_owner_required, admin_required

restaurant_bp = Blueprint('restaurant', __name__)

@restaurant_bp.route('/dashboard')
@restaurant_owner_required
def dashboard():
    """Restaurant owner dashboard"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Get restaurant owned by this user
        cursor.execute("SELECT * FROM restaurants WHERE owner_id = ?", (session['user_id'],))
        restaurant = cursor.fetchone()
        
        if not restaurant:
            return redirect(url_for('restaurant.onboard'))
        
        # Get today's orders
        cursor.execute("""
            SELECT COUNT(*) as today_orders 
            FROM orders 
            WHERE restaurant_id = ? AND DATE(created_at) = DATE('now')
        """, (restaurant['id'],))
        today_orders = cursor.fetchone()
        
        # Get total revenue
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total_revenue 
            FROM orders 
            WHERE restaurant_id = ? AND status = 'delivered'
        """, (restaurant['id'],))
        total_revenue = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('restaurant/dashboard.html',
                             restaurant=restaurant,
                             today_orders=today_orders['today_orders'],
                             total_revenue=total_revenue['total_revenue'])
    else:
        flash('Database connection error!', 'error')
        return render_template('restaurant/dashboard.html')

@restaurant_bp.route('/menu')
@restaurant_owner_required
def menu_management():
    """Manage restaurant menu"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM restaurants WHERE owner_id = ?", (session['user_id'],))
        restaurant = cursor.fetchone()
        
        if not restaurant:
            return redirect(url_for('restaurant.onboard'))
        
        cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ?", (restaurant['id'],))
        menu_items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('restaurant/menu_management.html',
                             restaurant=restaurant,
                             menu_items=menu_items)
    else:
        flash('Database connection error!', 'error')
        return render_template('restaurant/menu_management.html')

@restaurant_bp.route('/orders')
@restaurant_owner_required
def orders():
    """View restaurant orders"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM restaurants WHERE owner_id = ?", (session['user_id'],))
        restaurant = cursor.fetchone()
        
        if not restaurant:
            return redirect(url_for('restaurant.onboard'))
        
        cursor.execute("""
            SELECT o.*, u.name as customer_name 
            FROM orders o 
            JOIN users u ON o.customer_id = u.id 
            WHERE o.restaurant_id = ? 
            ORDER BY o.created_at DESC
        """, (restaurant['id'],))
        orders_raw = cursor.fetchall()
        
        # Format dates for template
        from datetime import datetime
        orders = []
        for order in orders_raw:
            order_dict = dict(order)
            created_at = order_dict.get('created_at')
            if created_at:
                # Handle both string and datetime objects
                if isinstance(created_at, str):
                    try:
                        # Try parsing common SQLite datetime formats
                        if 'T' in created_at:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        # If parsing fails, use the string as-is
                        order_dict['created_at_human'] = created_at
                    else:
                        order_dict['created_at_human'] = dt.strftime('%b %d, %Y at %I:%M %p')
                elif hasattr(created_at, 'strftime'):
                    order_dict['created_at_human'] = created_at.strftime('%b %d, %Y at %I:%M %p')
                else:
                    order_dict['created_at_human'] = str(created_at)
            else:
                order_dict['created_at_human'] = 'N/A'
            orders.append(order_dict)
        
        cursor.close()
        conn.close()
        
        return render_template('restaurant/orders.html',
                             restaurant=restaurant,
                             orders=orders)
    else:
        flash('Database connection error!', 'error')
        return render_template('restaurant/orders.html')

@restaurant_bp.route('/analytics')
@restaurant_owner_required
def analytics():
    """Restaurant analytics"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurants WHERE owner_id = %s", (session['user_id'],))
        restaurant = cursor.fetchone()
        cursor.close()
        conn.close()
        if not restaurant:
            return redirect(url_for('restaurant.onboard'))
        return render_template('restaurant/analytics.html', restaurant=restaurant)
    flash('Database connection error!', 'error')
    return redirect(url_for('restaurant.dashboard'))

@restaurant_bp.route('/predictions')
@restaurant_owner_required
def predictions():
    """AI predictions for restaurant"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM restaurants WHERE owner_id = ?", (session['user_id'],))
        restaurant = cursor.fetchone()
        cursor.close()
        conn.close()
        if not restaurant:
            return redirect(url_for('restaurant.onboard'))
        return redirect(url_for('ai.restaurant_predictions', restaurant_id=restaurant['id']))
    flash('Database connection error!', 'error')
    return redirect(url_for('restaurant.dashboard'))


@restaurant_bp.route('/onboard', methods=['GET', 'POST'])
@restaurant_owner_required
def onboard():
    """Allow restaurant owners to register their restaurant."""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return redirect(url_for('restaurant.dashboard'))

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants WHERE owner_id = ?", (session['user_id'],))
    existing = cursor.fetchone()
    if existing and request.method == 'GET':
        cursor.close()
        conn.close()
        flash('You already have a restaurant. Updating info coming soon.', 'info')
        return redirect(url_for('restaurant.dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        cuisine = request.form['cuisine_type']
        delivery_time = request.form.get('delivery_time', '30 mins')

        try:
            cursor.execute("""
                INSERT INTO restaurants (owner_id, name, cuisine_type, rating, is_approved, is_open, delivery_time)
                VALUES (?, ?, ?, 4.5, 1, 1, ?)
            """, (session['user_id'], name, cuisine, delivery_time))
            conn.commit()
            flash('Restaurant registered successfully!', 'success')
            return redirect(url_for('restaurant.dashboard'))
        except Exception as e:
            conn.rollback()
            flash(f'Error creating restaurant: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    else:
        cursor.close()
        conn.close()

    return render_template('restaurant/onboard.html')

# Menu Item API Endpoints
@restaurant_bp.route('/menu/item', methods=['POST'])
@restaurant_owner_required
def add_menu_item():
    """Add a new menu item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json() or {}
    except Exception:
        data = request.form.to_dict()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        # Get restaurant owned by this user
        cursor.execute("SELECT id FROM restaurants WHERE owner_id = ?", (session['user_id'],))
        restaurant = cursor.fetchone()
        
        if not restaurant:
            return jsonify({'success': False, 'message': 'Restaurant not found'}), 404
        
        # Insert menu item
        cursor.execute("""
            INSERT INTO menu_items (restaurant_id, name, category, price, description, is_available, is_vegetarian, is_spicy, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            restaurant['id'],
            data.get('name'),
            data.get('category'),
            float(data.get('price', 0)),
            data.get('description', ''),
            1,  # is_available
            1 if data.get('is_vegetarian') else 0,
            1 if data.get('is_spicy') else 0,
            data.get('image_url', '')
        ))
        
        conn.commit()
        item_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'message': 'Menu item added successfully',
            'item_id': item_id
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@restaurant_bp.route('/menu/item/<int:item_id>', methods=['PUT'])
@restaurant_owner_required
def update_menu_item(item_id):
    """Update a menu item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json() or {}
    except Exception:
        data = request.form.to_dict()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        # Verify ownership
        cursor.execute("""
            SELECT mi.id FROM menu_items mi
            JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.id = ? AND r.owner_id = ?
        """, (item_id, session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Menu item not found or access denied'}), 404
        
        # Update menu item
        cursor.execute("""
            UPDATE menu_items 
            SET name = ?, category = ?, price = ?, description = ?, 
                is_vegetarian = ?, is_spicy = ?, image_url = ?
            WHERE id = ?
        """, (
            data.get('name'),
            data.get('category'),
            float(data.get('price', 0)),
            data.get('description', ''),
            1 if data.get('is_vegetarian') else 0,
            1 if data.get('is_spicy') else 0,
            data.get('image_url', ''),
            item_id
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Menu item updated successfully'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@restaurant_bp.route('/menu/item/<int:item_id>', methods=['DELETE'])
@restaurant_owner_required
def delete_menu_item(item_id):
    """Delete a menu item"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        # Verify ownership
        cursor.execute("""
            SELECT mi.id FROM menu_items mi
            JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.id = ? AND r.owner_id = ?
        """, (item_id, session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Menu item not found or access denied'}), 404
        
        # Delete menu item
        cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Menu item deleted successfully'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@restaurant_bp.route('/menu/item/<int:item_id>/toggle', methods=['POST'])
@restaurant_owner_required
def toggle_menu_item_availability(item_id):
    """Toggle menu item availability"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        # Verify ownership
        cursor.execute("""
            SELECT mi.id, mi.is_available FROM menu_items mi
            JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.id = ? AND r.owner_id = ?
        """, (item_id, session['user_id']))
        
        item = cursor.fetchone()
        if not item:
            return jsonify({'success': False, 'message': 'Menu item not found or access denied'}), 404
        
        # Toggle availability
        new_availability = 0 if item['is_available'] else 1
        cursor.execute("UPDATE menu_items SET is_available = ? WHERE id = ?", (new_availability, item_id))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Availability updated successfully',
            'is_available': new_availability
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@restaurant_bp.route('/menu/item/<int:item_id>', methods=['GET'])
@restaurant_owner_required
def get_menu_item(item_id):
    """Get a menu item by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        # Verify ownership and get item
        cursor.execute("""
            SELECT mi.* FROM menu_items mi
            JOIN restaurants r ON mi.restaurant_id = r.id
            WHERE mi.id = ? AND r.owner_id = ?
        """, (item_id, session['user_id']))
        
        item = cursor.fetchone()
        if not item:
            return jsonify({'success': False, 'message': 'Menu item not found or access denied'}), 404
        
        return jsonify({
            'success': True,
            'item': dict(item)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()