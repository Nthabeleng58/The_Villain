# routes/customer_routes.py

from flask import (
    Blueprint, render_template, request, session,
    jsonify, flash, redirect, url_for
)
from datetime import datetime
from utils.database import get_db_connection
from utils.security import customer_required
from ai.villain_ai import get_ai_recommendations
from utils.blockchain import VillainBlockchain
from blockchain.smart_contracts import SmartContractExecutor

customer_bp = Blueprint('customer', __name__, url_prefix="/customer")


# ---------------------------
# CUSTOMER DASHBOARD
# ---------------------------
@customer_bp.route('/dashboard')
@customer_required
def dashboard():
    """Main customer dashboard with featured restaurants, recent orders, and AI recommendations."""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return render_template('customer/dashboard.html')

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone() or {'name': session.get('name', 'Villain User')}

        # Featured restaurants (top rated)
        cursor.execute("""
            SELECT * FROM restaurants
            WHERE is_approved = TRUE
            ORDER BY rating DESC
            LIMIT 6
        """)
        featured_restaurants = cursor.fetchall()

        # All approved restaurants
        cursor.execute("""
            SELECT * FROM restaurants
            WHERE is_approved = TRUE
            ORDER BY name
        """)
        all_restaurants = cursor.fetchall()

        # Recent orders for this user
        cursor.execute("""
            SELECT o.*, r.name AS restaurant_name
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
            LIMIT 3
        """, (session['user_id'],))
        recent_orders = cursor.fetchall()
        for order in recent_orders:
            created_at = order.get('created_at')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    order['created_at_human'] = created_at.strftime('%b %d, %Y')
                else:
                    order['created_at_human'] = str(created_at)[:10]
            else:
                order['created_at_human'] = ''

        # AI Recommended meals
        recommended_meals = get_ai_recommendations(session['user_id'], top_n=5)

    except Exception as e:
        flash(f"Error fetching dashboard data: {e}", 'error')
        featured_restaurants, all_restaurants, recent_orders = [], [], []
        recommended_meals = []
        user = {'name': session.get('name', 'Villain User')}
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'customer/dashboard.html',
        user=user,
        featured_restaurants=featured_restaurants,
        all_restaurants=all_restaurants,
        recent_orders=recent_orders,
        recommended_meals=recommended_meals
    )


@customer_bp.route('/quick-order', methods=['POST'])
@customer_required
def quick_order():
    """Generate a quick AI-powered order and record it on the blockchain."""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return redirect(url_for('customer.dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM restaurants
            WHERE is_approved = 1
            ORDER BY rating DESC
            LIMIT 1
        """)
        restaurant = cursor.fetchone()

        if not restaurant:
            flash('No approved restaurants available yet.', 'error')
            return redirect(url_for('customer.dashboard'))

        cursor.execute("""
            SELECT * FROM menu_items
            WHERE restaurant_id = ? AND is_available = 1
            ORDER BY RANDOM()
            LIMIT 2
        """, (restaurant['id'],))
        items = cursor.fetchall()

        if not items:
            flash('Selected restaurant has no menu items yet.', 'error')
            return redirect(url_for('customer.dashboard'))

        total_amount = sum(item['price'] for item in items)

        cursor.execute("""
            INSERT INTO orders (customer_id, restaurant_id, total_amount, status, delivery_address, special_instructions)
            VALUES (?, ?, ?, 'delivered', ?, ?)
        """, (
            session['user_id'],
            restaurant['id'],
            total_amount,
            'Auto-generated Villain address',
            'Quick AI order'
        ))
        order_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item['id'], 1, item['price']))

        # Prepare order data for smart contracts
        order_data = {
            'order_id': order_id,
            'customer_id': session['user_id'],
            'customer_name': session.get('name', 'Villain Customer'),
            'restaurant_id': restaurant['id'],
            'restaurant_name': restaurant['name'],
            'total_amount': float(total_amount),
            'items': [{
                'item_name': item['name'],
                'quantity': 1,
                'price': float(item['price'])
            } for item in items],
            'timestamp': str(datetime.now()),
            'payment_method': 'cash',
            'delivery_address': 'Auto-generated Villain address'
        }
        
        # Execute smart contracts
        contract_success, contract_result, contract_message = SmartContractExecutor.execute_order_contract(order_data)
        
        if contract_success:
            order_data['smart_contracts'] = contract_result
        
        # Add to blockchain
        blockchain = VillainBlockchain()
        blockchain.add_order_to_blockchain(order_data)

        conn.commit()
        flash('Order placed! Blockchain updated and GDPR data refreshed.', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Unable to process quick order: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('customer.dashboard'))


# ---------------------------
# RESTAURANT DETAILS
# ---------------------------
@customer_bp.route('/restaurant/<int:restaurant_id>')
@customer_required
def view_restaurant(restaurant_id):
    """View a single restaurant and its available menu items."""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return redirect(url_for('customer.dashboard'))

    reviews = []
    average_rating = 0
    total_reviews = 0

    try:
        cursor = conn.cursor()

        # Restaurant details
        cursor.execute(
            "SELECT * FROM restaurants WHERE id = ? AND is_approved = 1",
            (restaurant_id,)
        )
        restaurant = cursor.fetchone()
        if not restaurant:
            flash('Restaurant not found!', 'error')
            return redirect(url_for('customer.dashboard'))

        # Menu items
        cursor.execute("""
            SELECT * FROM menu_items
            WHERE restaurant_id = ? AND is_available = 1
            ORDER BY price ASC
        """, (restaurant_id,))
        menu_items = cursor.fetchall()

        cursor.execute("""
            SELECT r.id, r.comment, r.rating, r.created_at,
                   COALESCE(r.user_name, u.name, 'Villain Customer') as reviewer_name
            FROM reviews r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.restaurant_id = ?
            ORDER BY r.id DESC
        """, (restaurant_id,))
        reviews = cursor.fetchall()
        for review in reviews:
            created = review.get('created_at')
            if created:
                if hasattr(created, 'strftime'):
                    review['created_label'] = created.strftime('%b %d, %Y')
                else:
                    review['created_label'] = str(created)[:10]
            else:
                review['created_label'] = 'Recently'

        cursor.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_reviews
            FROM reviews
            WHERE restaurant_id = ?
        """, (restaurant_id,))
        stats = cursor.fetchone() or {'avg_rating': None, 'total_reviews': 0}
        average_rating = round(stats['avg_rating'], 1) if stats.get('avg_rating') else restaurant.get('rating', 0)
        total_reviews = stats.get('total_reviews', 0)

    except Exception as e:
        flash(f"Error fetching restaurant data: {e}", 'error')
        restaurant, menu_items, reviews = None, [], []
        average_rating, total_reviews = 0, 0
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'customer/restaurant.html',
        restaurant=restaurant,
        menu_items=menu_items,
        reviews=reviews,
        average_rating=average_rating,
        total_reviews=total_reviews
    )


@customer_bp.route('/restaurant/<int:restaurant_id>/review', methods=['POST'])
@customer_required
def submit_review(restaurant_id):
    """Allow customers to rate and review a restaurant."""
    rating = request.form.get('rating')
    comment = request.form.get('comment', '').strip()

    try:
        rating_value = float(rating)
    except (TypeError, ValueError):
        flash('Please choose a valid rating.', 'error')
        return redirect(url_for('customer.view_restaurant', restaurant_id=restaurant_id))

    if rating_value < 1 or rating_value > 5:
        flash('Ratings must be between 1 and 5.', 'error')
        return redirect(url_for('customer.view_restaurant', restaurant_id=restaurant_id))

    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return redirect(url_for('customer.view_restaurant', restaurant_id=restaurant_id))

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO reviews (user_id, user_name, restaurant_id, comment, rating)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session['user_id'],
            session.get('name', 'Villain Customer'),
            restaurant_id,
            comment or 'No comment provided.',
            rating_value
        ))

        cursor.execute("""
            SELECT AVG(rating) as avg_rating
            FROM reviews
            WHERE restaurant_id = ?
        """, (restaurant_id,))
        avg_row = cursor.fetchone()
        if avg_row and avg_row.get('avg_rating'):
            cursor.execute(
                "UPDATE restaurants SET rating = ? WHERE id = ?",
                (round(avg_row['avg_rating'], 1), restaurant_id)
            )

        conn.commit()
        flash('Thanks for sharing your experience!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Unable to save review: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('customer.view_restaurant', restaurant_id=restaurant_id))


# ---------------------------
# CART PAGE
# ---------------------------
@customer_bp.route('/cart')
@customer_required
def cart():
    return render_template('customer/cart.html')


# ---------------------------
# CHECKOUT PAGE
# ---------------------------
@customer_bp.route('/checkout')
@customer_required
def checkout():
    return render_template('customer/checkout.html')


# ---------------------------
# ORDER HISTORY
# ---------------------------
@customer_bp.route('/orders')
@customer_required
def orders():
    """List all past orders for the logged-in user."""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return render_template('customer/orders.html')

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, r.name AS restaurant_name
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        """, (session['user_id'],))
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
                        order_dict['created_at_time'] = created_at
                    else:
                        order_dict['created_at_human'] = dt.strftime('%b %d, %Y at %I:%M %p')
                        order_dict['created_at_time'] = dt.strftime('%I:%M %p')
                elif hasattr(created_at, 'strftime'):
                    order_dict['created_at_human'] = created_at.strftime('%b %d, %Y at %I:%M %p')
                    order_dict['created_at_time'] = created_at.strftime('%I:%M %p')
                else:
                    order_dict['created_at_human'] = str(created_at)
                    order_dict['created_at_time'] = str(created_at)
            else:
                order_dict['created_at_human'] = 'N/A'
                order_dict['created_at_time'] = 'N/A'
            orders.append(order_dict)
    except Exception as e:
        flash(f"Error fetching orders: {e}", 'error')
        orders = []
    finally:
        cursor.close()
        conn.close()

    return render_template('customer/orders.html', orders=orders)


# ---------------------------
# PROFILE PAGE
# ---------------------------
@customer_bp.route('/profile')
@customer_required
def profile():
    """View customer profile information."""
    conn = get_db_connection()
    if not conn:
        flash('Database connection error!', 'error')
        return render_template('customer/profile.html')

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
    except Exception as e:
        flash(f"Error fetching profile: {e}", 'error')
        user = None
    finally:
        cursor.close()
        conn.close()

        render_template('customer/profile.html', user=user)


# ---------------------------
# SECURE ORDERS (BLOCKCHAIN VIEW)
# ---------------------------
@customer_bp.route('/secure-orders')
@customer_required
def secure_orders():
    """View customer's blockchain-secured orders"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to view secure orders', 'error')
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    orders = []
    integrity_status = True
    integrity_message = "Blockchain integrity verified successfully"
    
    if not conn:
        flash('Database connection error!', 'error')
        return render_template('customer/secure_orders.html',
                             orders=orders,
                             integrity_status=integrity_status,
                             integrity_message=integrity_message)

    cursor = None
    try:
        cursor = conn.cursor()
        
        # Get user's orders that are on blockchain
        cursor.execute("""
            SELECT o.*, r.name AS restaurant_name, br.current_hash, br.previous_hash, br.timestamp as blockchain_timestamp
            FROM orders o
            JOIN restaurants r ON o.restaurant_id = r.id
            LEFT JOIN blockchain_records br ON o.id = br.order_id
            WHERE o.customer_id = ? AND o.status = 'delivered'
            ORDER BY o.created_at DESC
        """, (user_id,))
        orders = cursor.fetchall()
        
        # Get blockchain integrity status (only if there are orders)
        if orders:
            blockchain = VillainBlockchain()
            integrity_status, integrity_message = blockchain.verify_blockchain_integrity()
        
    except Exception as e:
        flash(f"Error fetching secure orders: {e}", 'error')
        orders = []
        integrity_status = False
        integrity_message = f"Unable to verify blockchain integrity: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('customer/secure_orders.html',
                         orders=orders,
                         integrity_status=integrity_status,
                         integrity_message=integrity_message)
