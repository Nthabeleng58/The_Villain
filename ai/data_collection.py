import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.database import get_db_connection

class VillainDataset:
    def __init__(self):
        self.sales_data = None
        self.user_interactions = None
        self.menu_data = None
    
    def collect_real_data(self):
        """Collect real data from the application database"""
        conn = get_db_connection(raw=True)
        if not conn:
            return None, None, None
        
        try:
            # Sales data for prediction
            sales_query = """
                SELECT 
                    DATE(o.created_at) as date,
                    r.id as restaurant_id,
                    r.name as restaurant_name,
                    r.cuisine_type,
                    CAST(strftime('%w', o.created_at) AS INTEGER) as day_of_week,
                    CAST(strftime('%m', o.created_at) AS INTEGER) as month,
                    COUNT(*) as order_count,
                    SUM(o.total_amount) as total_sales,
                    AVG(o.total_amount) as avg_order_value
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.id
                WHERE o.status = 'delivered'
                GROUP BY DATE(o.created_at), r.id, r.cuisine_type
                ORDER BY date DESC
            """
            self.sales_data = pd.read_sql(sales_query, conn)
            
            # User interactions for recommendations
            interactions_query = """
                SELECT 
                    u.id as user_id,
                    oi.menu_item_id as item_id,
                    mi.name as item_name,
                    mi.category as item_category,
                    mi.price,
                    r.cuisine_type,
                    COUNT(*) as order_count
                FROM users u
                JOIN orders o ON u.id = o.customer_id
                JOIN order_items oi ON o.id = oi.order_id
                JOIN menu_items mi ON oi.menu_item_id = mi.id
                JOIN restaurants r ON mi.restaurant_id = r.id
                WHERE o.status = 'delivered'
                GROUP BY u.id, oi.menu_item_id, mi.name, mi.category, mi.price, r.cuisine_type
            """
            self.user_interactions = pd.read_sql(interactions_query, conn)
            
            return self.sales_data, self.user_interactions, None
            
        except Exception as e:
            print(f"Error collecting data: {e}")
            return None, None, None
        finally:
            conn.close()
    
    def generate_sample_data(self):
        """Generate sample data for demonstration"""
        np.random.seed(42)
        
        # Sample restaurants matching The Villain theme
        restaurants = [
            'Dark Knight Diner', 'Villainous Vegan', 'Sinister Sushi',
            'Evil Burger Empire', 'Wicked Wings', 'Malicious Mexican'
        ]
        
        cuisines = ['Burger', 'Vegan', 'Asian', 'Mexican', 'American']
        
        # Generate 3 months of sales data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 3, 31)
        date_range = pd.date_range(start_date, end_date, freq='D')
        
        sales_records = []
        for date in date_range:
            for restaurant_id in range(1, 7):  # 6 restaurants
                # Base sales with day-of-week and seasonal patterns
                base_sales = 50 + (restaurant_id * 10)
                day_multiplier = 1.2 if date.weekday() >= 5 else 1.0  # Weekend boost
                
                order_count = max(1, int(np.random.poisson(8 * day_multiplier)))
                total_sales = max(20, np.random.normal(base_sales * day_multiplier, 15))
                
                sales_records.append({
                    'date': date,
                    'restaurant_id': restaurant_id,
                    'restaurant_name': restaurants[restaurant_id - 1],
                    'cuisine_type': cuisines[(restaurant_id - 1) % len(cuisines)],
                    'day_of_week': date.weekday(),
                    'month': date.month,
                    'order_count': order_count,
                    'total_sales': total_sales,
                    'avg_order_value': total_sales / order_count
                })
        
        self.sales_data = pd.DataFrame(sales_records)
        
        # Generate user interactions
        user_interactions = []
        for user_id in range(1, 51):  # 50 users
            for _ in range(np.random.randint(5, 15)):  # 5-15 interactions per user
                item_id = np.random.randint(1, 31)  # 30 menu items
                order_count = np.random.randint(1, 4)
                
                user_interactions.append({
                    'user_id': user_id,
                    'item_id': item_id,
                    'item_name': f'Menu Item {item_id}',
                    'item_category': np.random.choice(['Main', 'Appetizer', 'Dessert', 'Drink']),
                    'price': np.random.uniform(5, 25),
                    'cuisine_type': np.random.choice(cuisines),
                    'order_count': order_count
                })
        
        self.user_interactions = pd.DataFrame(user_interactions)
        
        return self.sales_data, self.user_interactions, None