import hashlib
import json
from datetime import datetime
from utils.database import get_db_connection

class VillainBlockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = {
            'index': 0,
            'timestamp': str(datetime.now()),
            'data': {
                'message': 'Genesis Block - The Villain Food-App Blockchain',
                'order_id': 0
            },
            'previous_hash': '0' * 64,
            'nonce': 0
        }
        genesis_block['hash'] = self.calculate_hash(genesis_block)
        self.chain.append(genesis_block)
    
    def calculate_hash(self, block):
        """Calculate SHA-256 hash of a block"""
        block_string = json.dumps(block, sort_keys=True, indent=2).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def get_latest_block(self):
        """Get the most recent block from database"""
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blockchain_records ORDER BY id DESC LIMIT 1")
            latest_block = cursor.fetchone()
            cursor.close()
            conn.close()
            return latest_block
        return None
    
    def add_order_to_blockchain(self, order_data):
        """Add a completed order to the blockchain"""
        try:
            # Get the latest block for previous hash
            latest_block = self.get_latest_block()
            previous_hash = latest_block['current_hash'] if latest_block else '0' * 64
            
            # Create new block
            new_block = {
                'index': latest_block['id'] + 1 if latest_block else 1,
                'timestamp': str(datetime.now()),
                'data': order_data,
                'previous_hash': previous_hash,
                'nonce': 0
            }
            
            # Calculate hash (simple proof of work)
            new_block['hash'] = self.mine_block(new_block)
            
            # Store in database
            self.store_block_in_db(new_block)
            
            # Add to local chain
            self.chain.append(new_block)
            
            return new_block
            
        except Exception as e:
            print(f"Blockchain error: {e}")
            return None
    
    def mine_block(self, block, difficulty=2):
        """Simple proof of work mechanism"""
        prefix = '0' * difficulty
        block_copy = block.copy()
        
        while True:
            hash_result = self.calculate_hash(block_copy)
            if hash_result[:difficulty] == prefix:
                return hash_result
            block_copy['nonce'] += 1
    
    def store_block_in_db(self, block):
        """Store blockchain record in database (SQLite compatible)"""
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO blockchain_records 
                (order_id, previous_hash, current_hash, block_data)
                VALUES (?, ?, ?, ?)
            """, (
                block['data'].get('order_id', 0),
                block['previous_hash'],
                block['hash'],
                json.dumps(block['data'])
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        return False
    
    def verify_blockchain_integrity(self):
        """Verify the entire blockchain hasn't been tampered with"""
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blockchain_records ORDER BY id")
        blocks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        integrity_report = []
        previous_hash = '0' * 64
        
        for i, block in enumerate(blocks):
            block_status = {
                'block_id': block['id'],
                'order_id': block['order_id'],
                'status': 'VALID',
                'issues': []
            }
            
            # Verify previous hash matches
            if block['previous_hash'] != previous_hash:
                block_status['status'] = 'TAMPERED'
                block_status['issues'].append(f"Previous hash mismatch. Expected: {previous_hash}, Got: {block['previous_hash']}")
            
            # Verify current hash is valid
            try:
                block_data = json.loads(block['block_data'])
                # Handle timestamp - could be string or datetime
                timestamp_str = block.get('timestamp', '')
                if hasattr(timestamp_str, 'isoformat'):
                    timestamp_str = timestamp_str.isoformat()
                elif not isinstance(timestamp_str, str):
                    timestamp_str = str(timestamp_str)
                
                test_block = {
                    'index': block['id'],
                    'timestamp': timestamp_str,
                    'data': block_data,
                    'previous_hash': block['previous_hash'],
                    'nonce': 0
                }
                calculated_hash = self.calculate_hash(test_block)
                if calculated_hash != block['current_hash']:
                    block_status['status'] = 'TAMPERED'
                    block_status['issues'].append(f"Hash mismatch. Expected: {calculated_hash}, Got: {block['current_hash']}")
            except Exception as e:
                block_status['status'] = 'TAMPERED'
                block_status['issues'].append(f"Block data parsing error: {e}")
            
            integrity_report.append(block_status)
            previous_hash = block['current_hash']
        
        # Check if any blocks were tampered with
        tampered_blocks = [block for block in integrity_report if block['status'] == 'TAMPERED']
        
        if tampered_blocks:
            return False, f"Blockchain integrity compromised. {len(tampered_blocks)} blocks tampered."
        else:
            return True, "Blockchain integrity verified successfully."