// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VillainOrderContract
 * @dev Smart contract for managing food delivery orders on Ethereum blockchain
 */
contract VillainOrderContract {
    
    // Order structure
    struct Order {
        uint256 orderId;
        address customer;
        address restaurant;
        uint256 totalAmount;
        OrderStatus status;
        uint256 timestamp;
        string deliveryAddress;
        bool isPaid;
        bool isDelivered;
    }
    
    // Order status enum
    enum OrderStatus {
        Pending,
        Confirmed,
        Preparing,
        Ready,
        InDelivery,
        Delivered,
        Cancelled
    }
    
    // Order items structure
    struct OrderItem {
        string itemName;
        uint256 quantity;
        uint256 price;
    }
    
    // Mapping to store orders
    mapping(uint256 => Order) public orders;
    mapping(uint256 => OrderItem[]) public orderItems;
    
    // Order counter
    uint256 public orderCounter;
    
    // Events
    event OrderCreated(
        uint256 indexed orderId,
        address indexed customer,
        address indexed restaurant,
        uint256 totalAmount,
        uint256 timestamp
    );
    
    event OrderStatusUpdated(
        uint256 indexed orderId,
        OrderStatus newStatus,
        uint256 timestamp
    );
    
    event PaymentReceived(
        uint256 indexed orderId,
        address indexed payer,
        uint256 amount,
        uint256 timestamp
    );
    
    event OrderDelivered(
        uint256 indexed orderId,
        address indexed customer,
        uint256 timestamp
    );
    
    // Modifiers
    modifier onlyValidOrder(uint256 _orderId) {
        require(orders[_orderId].orderId != 0, "Order does not exist");
        _;
    }
    
    modifier onlyCustomer(uint256 _orderId) {
        require(orders[_orderId].customer == msg.sender, "Only customer can perform this action");
        _;
    }
    
    /**
     * @dev Create a new order
     * @param _restaurant Restaurant address
     * @param _totalAmount Total order amount in wei
     * @param _deliveryAddress Delivery address
     */
    function createOrder(
        address _restaurant,
        uint256 _totalAmount,
        string memory _deliveryAddress
    ) public returns (uint256) {
        require(_restaurant != address(0), "Invalid restaurant address");
        require(_totalAmount > 0, "Order amount must be greater than 0");
        
        orderCounter++;
        
        Order memory newOrder = Order({
            orderId: orderCounter,
            customer: msg.sender,
            restaurant: _restaurant,
            totalAmount: _totalAmount,
            status: OrderStatus.Pending,
            timestamp: block.timestamp,
            deliveryAddress: _deliveryAddress,
            isPaid: false,
            isDelivered: false
        });
        
        orders[orderCounter] = newOrder;
        
        emit OrderCreated(
            orderCounter,
            msg.sender,
            _restaurant,
            _totalAmount,
            block.timestamp
        );
        
        return orderCounter;
    }
    
    /**
     * @dev Add items to an order
     * @param _orderId Order ID
     * @param _itemNames Array of item names
     * @param _quantities Array of quantities
     * @param _prices Array of prices
     */
    function addOrderItems(
        uint256 _orderId,
        string[] memory _itemNames,
        uint256[] memory _quantities,
        uint256[] memory _prices
    ) public onlyValidOrder(_orderId) onlyCustomer(_orderId) {
        require(
            _itemNames.length == _quantities.length && 
            _quantities.length == _prices.length,
            "Arrays length mismatch"
        );
        
        for (uint256 i = 0; i < _itemNames.length; i++) {
            orderItems[_orderId].push(OrderItem({
                itemName: _itemNames[i],
                quantity: _quantities[i],
                price: _prices[i]
            }));
        }
    }
    
    /**
     * @dev Update order status
     * @param _orderId Order ID
     * @param _newStatus New order status
     */
    function updateOrderStatus(
        uint256 _orderId,
        OrderStatus _newStatus
    ) public onlyValidOrder(_orderId) {
        require(
            msg.sender == orders[_orderId].restaurant || 
            msg.sender == orders[_orderId].customer,
            "Unauthorized to update order status"
        );
        
        orders[_orderId].status = _newStatus;
        
        if (_newStatus == OrderStatus.Delivered) {
            orders[_orderId].isDelivered = true;
            emit OrderDelivered(_orderId, orders[_orderId].customer, block.timestamp);
        }
        
        emit OrderStatusUpdated(_orderId, _newStatus, block.timestamp);
    }
    
    /**
     * @dev Process payment for an order
     * @param _orderId Order ID
     */
    function processPayment(uint256 _orderId) public payable onlyValidOrder(_orderId) onlyCustomer(_orderId) {
        require(!orders[_orderId].isPaid, "Order already paid");
        require(msg.value >= orders[_orderId].totalAmount, "Insufficient payment");
        
        orders[_orderId].isPaid = true;
        orders[_orderId].status = OrderStatus.Confirmed;
        
        // Transfer payment to restaurant
        payable(orders[_orderId].restaurant).transfer(orders[_orderId].totalAmount);
        
        // Refund excess payment
        if (msg.value > orders[_orderId].totalAmount) {
            payable(msg.sender).transfer(msg.value - orders[_orderId].totalAmount);
        }
        
        emit PaymentReceived(_orderId, msg.sender, orders[_orderId].totalAmount, block.timestamp);
        emit OrderStatusUpdated(_orderId, OrderStatus.Confirmed, block.timestamp);
    }
    
    /**
     * @dev Get order details
     * @param _orderId Order ID
     * @return Order struct
     */
    function getOrder(uint256 _orderId) public view onlyValidOrder(_orderId) returns (Order memory) {
        return orders[_orderId];
    }
    
    /**
     * @dev Get order items count
     * @param _orderId Order ID
     * @return Number of items
     */
    function getOrderItemsCount(uint256 _orderId) public view onlyValidOrder(_orderId) returns (uint256) {
        return orderItems[_orderId].length;
    }
    
    /**
     * @dev Get order item by index
     * @param _orderId Order ID
     * @param _index Item index
     * @return OrderItem struct
     */
    function getOrderItem(uint256 _orderId, uint256 _index) public view onlyValidOrder(_orderId) returns (OrderItem memory) {
        require(_index < orderItems[_orderId].length, "Item index out of bounds");
        return orderItems[_orderId][_index];
    }
    
    /**
     * @dev Complete order and mark as delivered
     * @param _orderId Order ID
     */
    function completeOrder(uint256 _orderId) public onlyValidOrder(_orderId) {
        require(orders[_orderId].isPaid, "Order must be paid first");
        require(
            msg.sender == orders[_orderId].restaurant || 
            msg.sender == orders[_orderId].customer,
            "Unauthorized to complete order"
        );
        
        orders[_orderId].status = OrderStatus.Delivered;
        orders[_orderId].isDelivered = true;
        
        emit OrderDelivered(_orderId, orders[_orderId].customer, block.timestamp);
        emit OrderStatusUpdated(_orderId, OrderStatus.Delivered, block.timestamp);
    }
}

