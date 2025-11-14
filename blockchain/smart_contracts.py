"""
Smart Contracts for Villain Food App Blockchain
Implements automated contract execution for order processing
Supports both local Python contracts and Ethereum Solidity contracts
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import Config

# Try to import Ethereum integration (optional)
try:
    from blockchain.ethereum_integration import ethereum
    ETHEREUM_AVAILABLE = ethereum.is_connected() and Config.USE_ETHEREUM
except ImportError:
    ETHEREUM_AVAILABLE = False
    ethereum = None


class OrderSmartContract:
    """
    Smart contract for order processing
    Automatically executes when order conditions are met
    """
    
    def __init__(self, order_data: Dict):
        self.order_id = order_data.get('order_id')
        self.customer_id = order_data.get('customer_id')
        self.restaurant_id = order_data.get('restaurant_id')
        self.total_amount = order_data.get('total_amount', 0)
        self.items = order_data.get('items', [])
        self.timestamp = order_data.get('timestamp', str(datetime.now()))
        self.status = 'pending'
        self.contract_hash = None
    
    def validate_order(self) -> Tuple[bool, str]:
        """Validate order meets contract requirements"""
        if not self.order_id:
            return False, "Order ID is required"
        
        if not self.customer_id:
            return False, "Customer ID is required"
        
        if not self.restaurant_id:
            return False, "Restaurant ID is required"
        
        if self.total_amount <= 0:
            return False, "Order total must be greater than 0"
        
        if not self.items or len(self.items) == 0:
            return False, "Order must contain at least one item"
        
        # Verify item totals match order total
        calculated_total = sum(item.get('price', 0) * item.get('quantity', 0) for item in self.items)
        if abs(calculated_total - self.total_amount) > 0.01:  # Allow small floating point differences
            return False, f"Order total mismatch. Expected {calculated_total}, got {self.total_amount}"
        
        return True, "Order validated successfully"
    
    def execute_payment_contract(self, payment_method: str) -> Tuple[bool, str]:
        """Execute payment smart contract"""
        if payment_method not in ['card', 'mpesa', 'cash']:
            return False, f"Invalid payment method: {payment_method}"
        
        # Simulate payment processing
        payment_status = {
            'card': 'processed',
            'mpesa': 'confirmed',
            'cash': 'pending_collection'
        }
        
        self.status = payment_status.get(payment_method, 'pending')
        return True, f"Payment contract executed: {payment_method}"
    
    def execute_delivery_contract(self, delivery_address: str) -> Tuple[bool, str]:
        """Execute delivery smart contract"""
        if not delivery_address or len(delivery_address.strip()) == 0:
            return False, "Delivery address is required"
        
        # Validate address format (basic check)
        if len(delivery_address) < 10:
            return False, "Delivery address too short"
        
        self.delivery_address = delivery_address
        return True, "Delivery contract executed"
    
    def calculate_contract_hash(self) -> str:
        """Calculate unique hash for this contract"""
        contract_data = {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'restaurant_id': self.restaurant_id,
            'total_amount': self.total_amount,
            'items': sorted(self.items, key=lambda x: x.get('item_name', '')),
            'timestamp': self.timestamp
        }
        contract_string = json.dumps(contract_data, sort_keys=True)
        self.contract_hash = hashlib.sha256(contract_string.encode()).hexdigest()
        return self.contract_hash
    
    def to_dict(self) -> Dict:
        """Convert contract to dictionary for blockchain storage"""
        return {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'restaurant_id': self.restaurant_id,
            'total_amount': self.total_amount,
            'items': self.items,
            'timestamp': self.timestamp,
            'status': self.status,
            'contract_hash': self.contract_hash or self.calculate_contract_hash()
        }


class PaymentSmartContract:
    """
    Smart contract for payment processing
    Handles payment verification and settlement
    """
    
    def __init__(self, order_id: int, amount: float, payment_method: str):
        self.order_id = order_id
        self.amount = amount
        self.payment_method = payment_method
        self.status = 'pending'
        self.transaction_id = None
        self.timestamp = str(datetime.now())
    
    def verify_payment(self) -> Tuple[bool, str]:
        """Verify payment meets contract requirements"""
        if self.amount <= 0:
            return False, "Payment amount must be greater than 0"
        
        if self.payment_method not in ['card', 'mpesa', 'cash']:
            return False, f"Invalid payment method: {payment_method}"
        
        # Generate transaction ID
        transaction_data = f"{self.order_id}_{self.amount}_{self.payment_method}_{self.timestamp}"
        self.transaction_id = hashlib.sha256(transaction_data.encode()).hexdigest()[:16]
        
        return True, f"Payment verified. Transaction ID: {self.transaction_id}"
    
    def execute_settlement(self) -> Tuple[bool, str]:
        """Execute payment settlement"""
        if self.status != 'pending':
            return False, f"Payment already {self.status}"
        
        # Simulate payment processing
        if self.payment_method == 'cash':
            self.status = 'pending_collection'
            return True, "Payment will be collected on delivery"
        else:
            self.status = 'settled'
            return True, f"Payment settled via {self.payment_method}"
    
    def to_dict(self) -> Dict:
        """Convert payment contract to dictionary"""
        return {
            'order_id': self.order_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'timestamp': self.timestamp
        }


class DeliverySmartContract:
    """
    Smart contract for delivery tracking
    Manages delivery status and verification
    """
    
    def __init__(self, order_id: int, delivery_address: str):
        self.order_id = order_id
        self.delivery_address = delivery_address
        self.status = 'pending'
        self.delivery_timestamp = None
        self.verification_code = None
    
    def generate_verification_code(self) -> str:
        """Generate delivery verification code"""
        code_data = f"{self.order_id}_{self.delivery_address}_{datetime.now()}"
        self.verification_code = hashlib.sha256(code_data.encode()).hexdigest()[:8].upper()
        return self.verification_code
    
    def update_delivery_status(self, new_status: str) -> Tuple[bool, str]:
        """Update delivery status"""
        valid_statuses = ['pending', 'preparing', 'ready', 'in_transit', 'delivered', 'failed']
        
        if new_status not in valid_statuses:
            return False, f"Invalid delivery status: {new_status}"
        
        self.status = new_status
        
        if new_status == 'delivered':
            self.delivery_timestamp = str(datetime.now())
            if not self.verification_code:
                self.generate_verification_code()
        
        return True, f"Delivery status updated to {new_status}"
    
    def verify_delivery(self, verification_code: str) -> Tuple[bool, str]:
        """Verify delivery completion"""
        if not self.verification_code:
            return False, "Verification code not generated"
        
        if verification_code.upper() != self.verification_code:
            return False, "Invalid verification code"
        
        if self.status != 'delivered':
            return False, f"Delivery status is {self.status}, not delivered"
        
        return True, "Delivery verified successfully"
    
    def to_dict(self) -> Dict:
        """Convert delivery contract to dictionary"""
        return {
            'order_id': self.order_id,
            'delivery_address': self.delivery_address,
            'status': self.status,
            'delivery_timestamp': self.delivery_timestamp,
            'verification_code': self.verification_code
        }


class SmartContractExecutor:
    """
    Executes smart contracts in the correct order
    Supports both Ethereum Solidity contracts and local Python contracts
    """
    
    @staticmethod
    def execute_order_contract(order_data: Dict, use_ethereum: bool = None) -> Tuple[bool, Dict, str]:
        """
        Execute complete order smart contract
        Supports both Ethereum Solidity contracts and local Python contracts
        
        Args:
            order_data: Order data dictionary
            use_ethereum: Force Ethereum usage (None = auto-detect)
        
        Returns: (success, result_dict, message)
        """
        if use_ethereum is None:
            use_ethereum = ETHEREUM_AVAILABLE
        
        # If Ethereum is available and enabled, try to use it
        if use_ethereum and ethereum and ethereum.is_connected():
            try:
                # Get restaurant address (should be stored in database)
                restaurant_address = order_data.get('restaurant_address', '0x0000000000000000000000000000000000000000')
                
                # Convert amount to Wei (1 ETH = 10^18 Wei)
                amount_wei = ethereum.eth_to_wei(float(order_data.get('total_amount', 0)))
                
                # Create order on Ethereum blockchain
                order_id = ethereum.create_order_on_blockchain(
                    restaurant_address=restaurant_address,
                    total_amount_wei=amount_wei,
                    delivery_address=order_data.get('delivery_address', '')
                )
                
                if order_id:
                    return True, {
                        'ethereum_order_id': order_id,
                        'blockchain': 'ethereum',
                        'contract_address': ethereum.order_contract_address,
                        'network': 'ethereum',
                        'timestamp': str(datetime.now())
                    }, f"Order created on Ethereum blockchain. Order ID: {order_id}"
            except Exception as e:
                print(f"Ethereum contract execution failed: {e}")
                # Fall back to local contracts
        
        # Execute local Python contracts (fallback or default)
        contract = OrderSmartContract(order_data)
        
        # Validate order
        is_valid, message = contract.validate_order()
        if not is_valid:
            return False, {}, message
        
        # Execute payment contract
        payment_method = order_data.get('payment_method', 'cash')
        payment_contract = PaymentSmartContract(
            contract.order_id,
            contract.total_amount,
            payment_method
        )
        
        payment_valid, payment_msg = payment_contract.verify_payment()
        if not payment_valid:
            return False, {}, f"Payment validation failed: {payment_msg}"
        
        payment_settled, settlement_msg = payment_contract.execute_settlement()
        if not payment_settled:
            return False, {}, f"Payment settlement failed: {settlement_msg}"
        
        # Execute delivery contract
        delivery_address = order_data.get('delivery_address', '')
        delivery_contract = DeliverySmartContract(contract.order_id, delivery_address)
        
        delivery_valid, delivery_msg = delivery_contract.update_delivery_status('pending')
        if not delivery_valid:
            return False, {}, f"Delivery contract failed: {delivery_msg}"
        
        # Calculate contract hash
        contract_hash = contract.calculate_contract_hash()
        
        # Prepare result
        result = {
            'order_contract': contract.to_dict(),
            'payment_contract': payment_contract.to_dict(),
            'delivery_contract': delivery_contract.to_dict(),
            'contract_hash': contract_hash,
            'blockchain': 'local_python',
            'execution_timestamp': str(datetime.now())
        }
        
        return True, result, "All smart contracts executed successfully"

