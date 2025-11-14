# Component Locations Guide

This document shows where Smart Contracts, Blockchain, and Cybersecurity components are located in the Villain Food App codebase.

## 📦 **SMART CONTRACTS**

### Main File:
- **`blockchain/smart_contracts.py`** - Complete smart contract implementation

### What's Inside:
1. **`OrderSmartContract`** - Validates and processes orders
2. **`PaymentSmartContract`** - Handles payment verification and settlement
3. **`DeliverySmartContract`** - Manages delivery tracking and verification
4. **`SmartContractExecutor`** - Executes all contracts in sequence

### Where It's Used:
- **`routes/order_routes.py`** (line 6) - Executes contracts when orders are completed
- **`routes/customer_routes.py`** (line 12) - Executes contracts for quick orders

### Usage Example:
```python
from blockchain.smart_contracts import SmartContractExecutor

# Execute complete order contract
contract_success, contract_result, contract_message = SmartContractExecutor.execute_order_contract(order_data)
```

---

## ⛓️ **BLOCKCHAIN**

### Main File:
- **`utils/blockchain.py`** - Blockchain implementation

### What's Inside:
1. **`VillainBlockchain`** class with:
   - `create_genesis_block()` - Creates the first block
   - `add_order_to_blockchain()` - Adds orders to blockchain
   - `mine_block()` - Proof of work mechanism
   - `store_block_in_db()` - Stores blocks in database
   - `verify_blockchain_integrity()` - Verifies chain hasn't been tampered

### Database Table:
- **`blockchain_records`** table in SQLite database stores:
  - `order_id` - Reference to order
  - `previous_hash` - Hash of previous block
  - `current_hash` - Hash of current block
  - `block_data` - JSON data of the order
  - `timestamp` - When block was created

### Where It's Used:
- **`routes/order_routes.py`** (line 4) - Adds completed orders to blockchain
- **`routes/customer_routes.py`** (line 11) - Adds quick orders to blockchain
- **`routes/admin_routes.py`** (line 4) - Admin blockchain verification

### Usage Example:
```python
from utils.blockchain import VillainBlockchain

blockchain = VillainBlockchain()
blockchain.add_order_to_blockchain(order_data)
```

---

## 🔒 **CYBERSECURITY**

### Main Files:
1. **`utils/security.py`** - Core security utilities
2. **`routes/security_routes.py`** - Security configuration routes

### What's Inside `utils/security.py`:
1. **`VillainSecurity`** class with:
   - `ROLE_PERMISSIONS` - Role-Based Access Control (RBAC) matrix
   - `hash_password()` - Password hashing with bcrypt
   - `check_password()` - Password verification
   - `validate_email()` - Email format validation
   - `validate_password_strength()` - Password strength requirements
   - `has_permission()` - Permission checking decorator

2. **Security Decorators:**
   - `@admin_required` - Admin-only access
   - `@restaurant_owner_required` - Restaurant owner access
   - `@customer_required` - Customer access

### What's Inside `routes/security_routes.py`:
1. **Security Configuration Dashboard** (`/security/configuration`)
   - Data classification (Public, Private, Confidential, Restricted)
   - GDPR compliance controls
   - Access control matrix

2. **API Endpoints:**
   - `/security/classification.json` - Data classification JSON
   - `/security/gdpr.json` - GDPR compliance JSON

### Where It's Used:
- **`routes/auth_routes.py`** - Authentication and password hashing
- **`routes/customer_routes.py`** - Customer access control
- **`routes/restaurant_routes.py`** - Restaurant owner access control
- **`routes/admin_routes.py`** - Admin access control
- **`routes/ai_routes.py`** - AI dashboard access control
- **`routes/gdpr_routes.py`** - GDPR data access control
- **`routes/order_routes.py`** - Order creation access control

### Usage Example:
```python
from utils.security import customer_required, admin_required, VillainSecurity

@customer_required
def my_customer_function():
    # Only customers can access this
    pass

@admin_required
def my_admin_function():
    # Only admins can access this
    pass
```

---

## 📊 **GDPR COMPLIANCE** (Related to Cybersecurity)

### Main File:
- **`routes/gdpr_routes.py`** - GDPR compliance routes

### What's Inside:
1. **Right to Access** (`/gdpr/my-data`) - View all user data
2. **Right to Portability** (`/gdpr/export-my-data`) - Export data as JSON
3. **Right to Erasure** (`/gdpr/delete-account`) - Anonymize user data

### Where It's Used:
- Customer dashboard links to GDPR portal
- Security configuration shows GDPR compliance status

---

## 🗂️ **FILE STRUCTURE**

```
villain-food-app/
├── blockchain/
│   └── smart_contracts.py          # Smart Contracts Implementation
│
├── utils/
│   ├── blockchain.py               # Blockchain Core
│   └── security.py                 # Cybersecurity Core
│
├── routes/
│   ├── security_routes.py          # Security Configuration Routes
│   ├── gdpr_routes.py              # GDPR Compliance Routes
│   ├── order_routes.py             # Uses Blockchain + Smart Contracts
│   └── customer_routes.py          # Uses Blockchain + Smart Contracts
│
└── docs/
    └── cybersecurity/
        ├── data_classification.csv  # Data Classification Spreadsheet
        └── gdpr_compliance.csv     # GDPR Compliance Spreadsheet
```

---

## 🔗 **HOW THEY WORK TOGETHER**

1. **Order Flow:**
   - Customer places order → Smart Contract validates → Order created → Added to Blockchain

2. **Security Flow:**
   - User authenticates → Security module checks permissions → Access granted/denied

3. **GDPR Flow:**
   - User requests data → Security checks authentication → GDPR routes provide data

4. **Blockchain Verification:**
   - Admin verifies integrity → Blockchain module checks all blocks → Reports any tampering

---

## 🚀 **QUICK ACCESS**

### To View Smart Contracts:
```bash
# Open the file
blockchain/smart_contracts.py
```

### To View Blockchain:
```bash
# Open the file
utils/blockchain.py
```

### To View Cybersecurity:
```bash
# Core security
utils/security.py

# Security configuration
routes/security_routes.py
```

### To Access Security Dashboard:
```
http://localhost:5000/security/configuration
(Admin login required)
```

### To Access GDPR Portal:
```
http://localhost:5000/gdpr/my-data
(Customer login required)
```

### To Verify Blockchain:
```
http://localhost:5000/admin/blockchain-verify
(Admin login required)
```

