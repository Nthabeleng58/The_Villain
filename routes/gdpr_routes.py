from flask import Blueprint, render_template, request, session, jsonify, send_file, current_app, redirect, url_for, flash
import json
from io import BytesIO
from datetime import datetime
from utils.database import get_db_connection
from utils.security import customer_required

gdpr_bp = Blueprint('gdpr', __name__)

@gdpr_bp.route('/my-data')
@customer_required
def view_my_data():
    """GDPR Right to Access - User can view all their data"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to view your data', 'error')
        return redirect(url_for('auth.login'))
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor()
        
        # Get personal data
        cursor.execute("""
            SELECT id, email, name, phone, role, loyalty_points, created_at 
            FROM users WHERE id = ?
        """, (user_id,))
        personal_data = cursor.fetchone()
        
        # Get order history
        cursor.execute("""
            SELECT o.*, r.name as restaurant_name 
            FROM orders o 
            JOIN restaurants r ON o.restaurant_id = r.id 
            WHERE o.customer_id = ?
            ORDER BY o.created_at DESC
        """, (user_id,))
        orders_data = cursor.fetchall()
        
        # Convert to list of dicts for JSON serialization
        orders_list = []
        for order in orders_data:
            created_at = order.get('created_at')
            if created_at:
                if hasattr(created_at, 'isoformat'):
                    created_at_str = created_at.isoformat()
                elif hasattr(created_at, 'strftime'):
                    created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    created_at_str = str(created_at)
            else:
                created_at_str = None
            
            orders_list.append({
                'id': order['id'],
                'restaurant_name': order['restaurant_name'],
                'total_amount': float(order['total_amount']),
                'status': order['status'],
                'created_at': created_at_str
            })
        
        cursor.close()
        conn.close()
        
        return render_template('gdpr/data_portal.html',
                             personal_data=personal_data,
                             orders_data=orders_list)
    else:
        return jsonify({'success': False, 'message': 'Database connection error'})

@gdpr_bp.route('/export-my-data')
@customer_required
def export_my_data():
    """GDPR Data Portability - Export user data as JSON"""
    user_id = session['user_id']
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor()
        
        # Get all user data
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        cursor.execute("""
            SELECT o.*, r.name as restaurant_name 
            FROM orders o 
            JOIN restaurants r ON o.restaurant_id = r.id 
            WHERE o.customer_id = ?
        """, (user_id,))
        orders_data = cursor.fetchall()
        
        cursor.execute("SELECT * FROM reviews WHERE user_id = ?", (user_id,))
        reviews_data = cursor.fetchall()
        
        # Prepare export data
        export_data = {
            'user_profile': user_data,
            'order_history': orders_data,
            'reviews': reviews_data,
            'exported_at': datetime.now().isoformat()
        }
        
        cursor.close()
        conn.close()
        
        # Create JSON file
        json_data = json.dumps(export_data, indent=2, default=str)
        return current_app.send_file(
            BytesIO(json_data.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'villain_food_app_data_{user_id}.json'
        )
    else:
        return jsonify({'success': False, 'message': 'Database connection error'})

@gdpr_bp.route('/delete-account', methods=['POST'])
@customer_required
def delete_account():
    """GDPR Right to Erasure - Anonymize user data"""
    user_id = session['user_id']
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor()
        
        try:
            # Anonymize user data (don't delete for order history integrity)
            cursor.execute("""
                UPDATE users 
                SET email = ?,
                    name = 'Deleted User',
                    phone = NULL,
                    password_hash = 'deleted',
                    avatar_url = NULL
                WHERE id = ?
            """, (f'deleted_{user_id}@villain-food.com', user_id))
            
            # Anonymize reviews
            cursor.execute("""
                UPDATE reviews 
                SET user_name = 'Anonymous',
                    comment = 'This review has been removed by user request'
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            
            # Clear session
            session.clear()
            
            return jsonify({
                'success': True,
                'message': 'Your account has been anonymized in compliance with GDPR Right to Erasure'
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': f'Error processing request: {str(e)}'
            })
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'message': 'Database connection error'})