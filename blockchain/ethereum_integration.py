"""
Ethereum Blockchain Integration for Villain Food App
Handles Web3 interactions, contract deployment, and transaction management
"""

import os
import json
from typing import Dict, Optional, Tuple, List
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from config import Config


class EthereumIntegration:
    """Handle Ethereum blockchain interactions"""
    
    def __init__(self):
        self.w3 = None
        self.account = None
        self.order_contract = None
        self.token_contract = None
        self.order_contract_address = None
        self.token_contract_address = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Web3 connection to Ethereum network"""
        # Get network configuration from environment or config
        network_url = os.environ.get('ETHEREUM_RPC_URL', 'http://localhost:8545')
        private_key = os.environ.get('ETHEREUM_PRIVATE_KEY', '')
        
        try:
            # Connect to Ethereum node
            self.w3 = Web3(Web3.HTTPProvider(network_url))
            
            # For PoA networks (like Polygon, BSC testnet)
            if 'polygon' in network_url.lower() or 'bsc' in network_url.lower():
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            if not self.w3.is_connected():
                print("Warning: Could not connect to Ethereum network")
                return
            
            # Set up account if private key provided
            if private_key:
                self.account = Account.from_key(private_key)
                print(f"Connected to Ethereum. Account: {self.account.address}")
            else:
                print("No private key provided. Contract deployment disabled.")
                
        except Exception as e:
            print(f"Error initializing Ethereum connection: {e}")
            print("Falling back to local blockchain simulation")
    
    def is_connected(self) -> bool:
        """Check if connected to Ethereum network"""
        return self.w3 is not None and self.w3.is_connected()
    
    def get_balance(self, address: Optional[str] = None) -> float:
        """Get ETH balance for an address"""
        if not self.is_connected():
            return 0.0
        
        addr = address or (self.account.address if self.account else None)
        if not addr:
            return 0.0
        
        try:
            balance_wei = self.w3.eth.get_balance(addr)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            print(f"Error getting balance: {e}")
            return 0.0
    
    def load_contract(self, contract_address: str, abi_path: str):
        """Load a deployed contract"""
        if not self.is_connected():
            return None
        
        try:
            with open(abi_path, 'r') as f:
                abi = json.load(f)
            
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            return contract
        except Exception as e:
            print(f"Error loading contract: {e}")
            return None
    
    def deploy_order_contract(self) -> Optional[str]:
        """Deploy OrderContract to Ethereum"""
        if not self.is_connected() or not self.account:
            print("Cannot deploy: Not connected or no account")
            return None
        
        try:
            # Load contract bytecode and ABI
            contract_path = os.path.join(
                os.path.dirname(__file__),
                'contracts',
                'VillainOrderContract.json'
            )
            
            if not os.path.exists(contract_path):
                print(f"Contract file not found: {contract_path}")
                print("Please compile the Solidity contract first")
                return None
            
            with open(contract_path, 'r') as f:
                contract_data = json.load(f)
            
            bytecode = contract_data['bytecode']
            abi = contract_data['abi']
            
            # Create contract instance
            contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Build transaction
            transaction = contract.constructor().build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 3000000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.order_contract_address = tx_receipt.contractAddress
            self.order_contract = self.w3.eth.contract(
                address=self.order_contract_address,
                abi=abi
            )
            
            print(f"Order contract deployed at: {self.order_contract_address}")
            return self.order_contract_address
            
        except Exception as e:
            print(f"Error deploying order contract: {e}")
            return None
    
    def create_order_on_blockchain(
        self,
        restaurant_address: str,
        total_amount_wei: int,
        delivery_address: str
    ) -> Optional[int]:
        """Create an order on Ethereum blockchain"""
        if not self.is_connected() or not self.order_contract or not self.account:
            return None
        
        try:
            # Build transaction
            transaction = self.order_contract.functions.createOrder(
                restaurant_address,
                total_amount_wei,
                delivery_address
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get order ID from event
            order_id = None
            if tx_receipt.logs:
                event = self.order_contract.events.OrderCreated().process_receipt(tx_receipt)
                if event:
                    order_id = event[0]['args']['orderId']
            
            return order_id
            
        except Exception as e:
            print(f"Error creating order on blockchain: {e}")
            return None
    
    def process_payment(self, order_id: int, amount_wei: int) -> bool:
        """Process payment for an order using ETH"""
        if not self.is_connected() or not self.order_contract or not self.account:
            return False
        
        try:
            transaction = self.order_contract.functions.processPayment(order_id).build_transaction({
                'from': self.account.address,
                'value': amount_wei,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return tx_receipt.status == 1
            
        except Exception as e:
            print(f"Error processing payment: {e}")
            return False
    
    def get_order_status(self, order_id: int) -> Optional[Dict]:
        """Get order status from blockchain"""
        if not self.is_connected() or not self.order_contract:
            return None
        
        try:
            order = self.order_contract.functions.getOrder(order_id).call()
            return {
                'orderId': order[0],
                'customer': order[1],
                'restaurant': order[2],
                'totalAmount': order[3],
                'status': order[4],
                'timestamp': order[5],
                'isPaid': order[6],
                'isDelivered': order[7]
            }
        except Exception as e:
            print(f"Error getting order status: {e}")
            return None
    
    def eth_to_wei(self, eth_amount: float) -> int:
        """Convert ETH to Wei"""
        if not self.is_connected():
            return 0
        return self.w3.to_wei(eth_amount, 'ether')
    
    def wei_to_eth(self, wei_amount: int) -> float:
        """Convert Wei to ETH"""
        if not self.is_connected():
            return 0.0
        return float(self.w3.from_wei(wei_amount, 'ether'))


# Global instance
ethereum = EthereumIntegration()

