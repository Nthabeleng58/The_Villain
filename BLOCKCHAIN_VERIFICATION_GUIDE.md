# How to Verify Blockchain is Working

## Overview
The Villain Food-App uses blockchain technology to create an immutable record of all delivered orders. Here's how to see and verify it's working.

## Step-by-Step Verification

### Method 1: Customer View - Secure Orders Page

1. **Login as a Customer**
   - Go to the login page
   - Login with your customer account

2. **Place and Complete an Order**
   - Add items to cart
   - Go to checkout and place an order
   - The order will be automatically added to blockchain when it's marked as "delivered"

3. **View Blockchain-Protected Orders**
   - Navigate to: **Customer Dashboard → Secure Orders** tab
   - Or go directly to: `/customer/secure-orders`
   - You'll see:
     - ✅ **Blockchain Status**: Shows if the blockchain is verified
     - **Block Hash**: Unique hash for each order block
     - **Previous Hash**: Links to the previous block (creates the chain)
     - **Blockchain Timestamp**: When the order was added to blockchain
     - **Status**: "Immutable & Verified" badge

### Method 2: Admin View - Blockchain Verification

1. **Login as Admin**
   - Login with an admin account

2. **Access Blockchain Verification**
   - Go to: **Admin Dashboard → Blockchain Verify**
   - Or navigate to: `/admin/blockchain/verify`
   - You'll see:
     - ✅ **Ledger Verified** (green checkmark) - Blockchain is intact
     - ⚠️ **Tampering Detected** (red warning) - If any blocks were modified
     - **Verification Message**: Details about the blockchain state

3. **Re-run Verification**
   - Click "Re-run Verification" to check blockchain integrity again
   - This verifies all blocks are properly chained and not tampered with

## What to Look For

### ✅ Signs Blockchain is Working:

1. **Block Hashes Present**
   - Each delivered order should have a unique block hash (64-character hexadecimal string)
   - Example: `a3f5b2c1d4e6f7a8b9c0d1e2f3a4b5c6...`

2. **Previous Hash Links**
   - Each block (except the first) should have a previous hash
   - This creates the "chain" - each block links to the previous one
   - First block shows "Genesis" as previous hash

3. **Integrity Status**
   - Should show "Verified" or "Ledger Verified" in green
   - This means all blocks are properly linked and not tampered with

4. **Blockchain Timestamp**
   - Shows when the order was added to blockchain
   - Should match or be close to the order completion time

### ⚠️ If Blockchain is NOT Working:

- Orders show "This order will be added to the blockchain when it's delivered"
- No block hash is displayed
- Integrity status shows "Warning" or "Tampering Detected"
- Previous hash is missing or doesn't match

## Testing the Blockchain

### Quick Test:

1. **Place a Test Order:**
   ```
   1. Login as customer
   2. Add items to cart
   3. Complete checkout
   4. Order will be created
   ```

2. **Complete the Order:**
   - The order is automatically added to blockchain when status becomes "delivered"
   - This happens in the order completion flow

3. **Verify in Secure Orders:**
   ```
   1. Go to Customer Dashboard
   2. Click "Secure Orders" tab
   3. Find your completed order
   4. Check for:
      - Block Hash (should be visible)
      - Previous Hash (should link to previous block)
      - "Immutable & Verified" status
   ```

4. **Verify in Admin Panel:**
   ```
   1. Login as admin
   2. Go to /admin/blockchain/verify
   3. Should see "Ledger Verified" with green checkmark
   ```

## Understanding the Blockchain Data

### Block Structure:
Each block contains:
- **Index**: Block number in the chain
- **Timestamp**: When the block was created
- **Data**: Order information (order_id, customer, restaurant, items, total, etc.)
- **Previous Hash**: Hash of the previous block (creates the chain)
- **Current Hash**: SHA-256 hash of this block (includes previous hash)
- **Nonce**: Proof-of-work value (ensures hash starts with zeros)

### How It Works:
1. When an order is delivered, it's added to the blockchain
2. The system calculates a hash of the order data
3. The hash includes the previous block's hash (creating the chain)
4. Proof-of-work is performed (hash must start with "00")
5. Block is stored in `blockchain_records` table
6. Any tampering breaks the chain (detected by verification)

## Database Location

Blockchain records are stored in:
- **Table**: `blockchain_records`
- **Columns**:
  - `id`: Block index
  - `order_id`: Associated order
  - `previous_hash`: Previous block's hash
  - `current_hash`: This block's hash
  - `block_data`: JSON of order data
  - `timestamp`: When block was created

## Troubleshooting

### No Blockchain Records Showing:
- Make sure orders are marked as "delivered"
- Check that order completion flow is working
- Verify database connection

### Integrity Check Fails:
- Check database for corrupted records
- Verify all blocks have proper previous_hash links
- Re-run verification to see specific error messages

### Block Hash Not Displaying:
- Order might not be delivered yet
- Check if order status is "delivered"
- Verify blockchain_records table has entry for that order_id

## Additional Features

### Smart Contracts:
- Orders also execute smart contracts before blockchain recording
- Check order completion logs for smart contract execution messages

### Export Ledger:
- Admins can export blockchain snapshot
- Available from blockchain verification page

## Summary

**To see blockchain working:**
1. ✅ Place and complete an order (as customer)
2. ✅ View it in "Secure Orders" page (should show block hash)
3. ✅ Check admin "Blockchain Verify" page (should show "Verified")
4. ✅ Verify each block links to previous block (chain integrity)

The blockchain creates an **immutable audit trail** of all delivered orders, ensuring data integrity and transparency!

