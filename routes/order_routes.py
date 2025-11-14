from flask import Blueprint, request, jsonify, session
from datetime import datetime
from utils.database import get_db_connection
from utils.blockchain import VillainBlockchain
from utils.security import customer_required
from blockchain.smart_contracts import SmartContractExecutor

order_bp = Blueprint('order', __name__, url_prefix='/order')
blockchain = VillainBlockchain()

@order_bp.route('/create', methods=['POST'])
@customer_required
def create_order():
    """Create a new order"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        data = request.get_json() or {}
    except Exception as e:
        return jsonify({'success': False, 'message': f'Invalid JSON data: {str(e)}'}), 400
    
    restaurant_id = data.get('restaurant_id')
    items = data.get('items', [])
    delivery_address = data.get('delivery_address', '')
    special_instructions = data.get('special_instructions', '')
    payment_method = data.get('payment_method', 'cash')
    crypto_tx_hash = data.get('crypto_tx_hash', None)  # MetaMask transaction hash
    
    if not restaurant_id:
        return jsonify({'success': False, 'message': 'Restaurant ID is required'}), 400
    
    if not items:
        return jsonify({'success': False, 'message': 'No items in order'}), 400
    
    # Use provided total_amount or calculate it
    total_amount = data.get('total_amount')
    if not total_amount:
        # Calculate total amount
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        delivery_fee = 2.99
        tax = subtotal * 0.08
        total_amount = subtotal + delivery_fee + tax
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        try:
            # Create order
            # Store crypto transaction hash in special_instructions if crypto payment
            final_instructions = special_instructions
            if payment_method == 'crypto' and crypto_tx_hash:
                final_instructions = f"{special_instructions}\n[Crypto Payment TX: {crypto_tx_hash}]".strip()
            
            cursor.execute("""
                INSERT INTO orders (customer_id, restaurant_id, total_amount, delivery_address, special_instructions, status, payment_method)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """, (session['user_id'], restaurant_id, total_amount, delivery_address, final_instructions, payment_method))
            
            order_id = cursor.lastrowid
            
            # Add order items
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                """, (order_id, item['menu_item_id'], item['quantity'], item['price']))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Order created successfully',
                'order_id': order_id
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': f'Order creation failed: {str(e)}'})
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'message': 'Database connection error'})

@order_bp.route('/complete/<int:order_id>', methods=['POST'])
@customer_required
def complete_order(order_id):
    """Mark order as delivered and add to blockchain"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        try:
            # Get order details for blockchain
            cursor.execute("""
                SELECT o.*, r.name as restaurant_name, u.name as customer_name
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.id
                JOIN users u ON o.customer_id = u.id
                WHERE o.id = ?
            """, (order_id,))
            order = cursor.fetchone()
            
            if not order:
                return jsonify({'success': False, 'message': 'Order not found'})
            
            # Get order items
            cursor.execute("""
                SELECT oi.*, mi.name as item_name
                FROM order_items oi
                JOIN menu_items mi ON oi.menu_item_id = mi.id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = cursor.fetchall()
            
            # Update order status to delivered
            cursor.execute("UPDATE orders SET status = 'delivered' WHERE id = ?", (order_id,))
            
            # Prepare blockchain data
            blockchain_data = {
                'order_id': order_id,
                'customer_id': order['customer_id'],
                'customer_name': order['customer_name'],
                'restaurant_id': order['restaurant_id'],
                'restaurant_name': order['restaurant_name'],
                'total_amount': float(order['total_amount']),
                'items': [{
                    'item_name': item['item_name'],
                    'quantity': item['quantity'],
                    'price': float(item['price'])
                } for item in items],
                'timestamp': str(datetime.now()),
                'payment_method': order.get('payment_method', 'cash'),
                'delivery_address': order.get('delivery_address', '')
            }
            
            # Execute smart contracts
            contract_success, contract_result, contract_message = SmartContractExecutor.execute_order_contract(blockchain_data)
            
            if not contract_success:
                return jsonify({
                    'success': False,
                    'message': f'Smart contract execution failed: {contract_message}'
                })
            
            # Add contract result to blockchain data
            blockchain_data['smart_contracts'] = contract_result
            
            # Add to blockchain
            blockchain_result = blockchain.add_order_to_blockchain(blockchain_data)
            
            conn.commit()
            
            if blockchain_result:
                return jsonify({
                    'success': True,
                    'message': 'Order completed and added to blockchain',
                    'block_hash': blockchain_result['hash']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Order completed but blockchain recording failed'
                })
                
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'message': 'Database connection error'})

@order_bp.route('/status/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json() or {}
    except Exception as e:
        return jsonify({'success': False, 'message': f'Invalid JSON data: {str(e)}'}), 400
    
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'in_delivery', 'delivered', 'cancelled']
    
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Order status updated to {new_status}'
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'message': 'Database connection error'})