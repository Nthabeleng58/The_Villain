# Ethereum Integration Guide

This guide explains how to use Solidity smart contracts and Ethereum blockchain integration in the Villain Food App.

## 📋 Prerequisites

1. **Python Packages**
   ```bash
   pip install web3 eth-account py-solc-x
   ```

2. **Ethereum Node Access**
   - Local node (Ganache, Hardhat)
   - Testnet (Sepolia, Goerli)
   - Mainnet (requires real ETH)

## 🔧 Configuration

Set environment variables in `.env` file:

```env
# Ethereum Network Configuration
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
# OR for local: http://localhost:8545

# Private Key (NEVER commit to git!)
ETHEREUM_PRIVATE_KEY=your_private_key_here

# Contract Addresses (auto-populated after deployment)
ORDER_CONTRACT_ADDRESS=0x...
TOKEN_CONTRACT_ADDRESS=0x...
```

## 📁 File Structure

```
blockchain/
├── contracts/
│   ├── VillainOrderContract.sol    # Order management contract
│   ├── VillainToken.sol            # ERC-20 token contract
│   ├── VillainOrderContract.json    # Compiled contract (generated)
│   └── VillainToken.json            # Compiled contract (generated)
├── ethereum_integration.py          # Web3 integration
├── deploy_contracts.py              # Deployment script
└── smart_contracts.py               # Python bridge layer
```

## 🚀 Deployment Steps

### 1. Compile Contracts

```bash
python blockchain/deploy_contracts.py
```

This will:
- Compile Solidity contracts
- Generate ABI and bytecode files
- Save compiled contracts to JSON

### 2. Deploy to Network

The deployment script will automatically:
- Connect to Ethereum network
- Deploy OrderContract
- Save contract addresses

### 3. Update Configuration

Contract addresses are saved in `blockchain/contracts/deployment.json`

## 💰 Supported Cryptocurrencies

### 1. **Ethereum (ETH)**
- Native currency for transactions
- Used for order payments
- Gas fees paid in ETH

### 2. **Villain Food Token (VFT)**
- ERC-20 token
- Custom token for rewards and payments
- Can be minted for loyalty rewards

## 🔄 Usage Examples

### Create Order on Blockchain

```python
from blockchain.ethereum_integration import ethereum

# Convert price to Wei
amount_wei = ethereum.eth_to_wei(0.1)  # 0.1 ETH

# Create order
order_id = ethereum.create_order_on_blockchain(
    restaurant_address="0x...",
    total_amount_wei=amount_wei,
    delivery_address="123 Main St"
)
```

### Process Payment

```python
# Process ETH payment
success = ethereum.process_payment(
    order_id=1,
    amount_wei=ethereum.eth_to_wei(0.1)
)
```

### Check Order Status

```python
order_status = ethereum.get_order_status(order_id=1)
print(f"Order Status: {order_status['status']}")
print(f"Is Paid: {order_status['isPaid']}")
```

## 🔐 Security Notes

1. **Private Keys**: Never commit private keys to version control
2. **Testnet First**: Always test on testnet before mainnet
3. **Gas Limits**: Set appropriate gas limits to avoid failed transactions
4. **Error Handling**: Always handle transaction failures gracefully

## 🌐 Network Options

### Local Development
```env
ETHEREUM_RPC_URL=http://localhost:8545
```

### Sepolia Testnet (Recommended for Testing)
```env
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
```

### Mainnet (Production)
```env
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
```

## 📊 Contract Functions

### VillainOrderContract

- `createOrder()` - Create new order
- `addOrderItems()` - Add items to order
- `processPayment()` - Process ETH payment
- `updateOrderStatus()` - Update order status
- `completeOrder()` - Mark order as delivered
- `getOrder()` - Get order details

### VillainToken (ERC-20)

- `transfer()` - Transfer tokens
- `approve()` - Approve spending
- `mint()` - Create new tokens (owner only)
- `burn()` - Destroy tokens

## 🐛 Troubleshooting

### Connection Issues
- Check RPC URL is correct
- Verify network is accessible
- Check firewall settings

### Deployment Failures
- Ensure account has sufficient ETH for gas
- Check gas price settings
- Verify contract compilation succeeded

### Transaction Failures
- Check account balance
- Verify gas limit is sufficient
- Check contract address is correct

## 📚 Additional Resources

- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [Solidity Documentation](https://docs.soliditylang.org/)
- [Ethereum Developer Resources](https://ethereum.org/en/developers/)

