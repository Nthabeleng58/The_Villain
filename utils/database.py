import os
import sqlite3
from config import Config


class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        sql = self._normalize_query(query)
        parameters = params or []
        self._cursor.execute(sql, parameters)
        return self

    def executemany(self, query, seq_of_params):
        sql = self._normalize_query(query)
        self._cursor.executemany(sql, seq_of_params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self._cursor.close()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def _normalize_query(self, query):
        sql = query.replace('%s', '?')
        sql = sql.replace('TRUE', '1').replace('FALSE', '0')
        sql = sql.replace('NOW()', "CURRENT_TIMESTAMP")
        sql = sql.replace('CURDATE()', "DATE('now')")
        return sql


class SQLiteConnectionWrapper:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        # dictionary flag retained for compatibility
        return SQLiteCursorWrapper(self._connection.cursor())

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()

    def __getattr__(self, item):
        return getattr(self._connection, item)


def get_db_connection(raw=False):
    """Create and return SQLite database connection"""
    try:
        os.makedirs(os.path.dirname(Config.SQLITE_DB_PATH), exist_ok=True)
        connection = sqlite3.connect(Config.SQLITE_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        connection.row_factory = sqlite3.Row
        if raw:
            return connection
        return SQLiteConnectionWrapper(connection)
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


def init_db():
    """Initialize SQLite database with tables and sample data"""
    print("Initializing database...")
    conn = get_db_connection(raw=True)
    if not conn:
        print("Database connection failed!")
        return

    try:
        cursor = conn.cursor()
        cursor.executescript(_schema_sql())
        ensure_schema_updates(cursor)
        seed_sample_data(cursor)
        conn.commit()
        print("Database ready at", Config.SQLITE_DB_PATH)
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database initialization error: {e}")
    finally:
        cursor.close()
        conn.close()


def _schema_sql():
    return """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        role TEXT NOT NULL,
        loyalty_points INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        name TEXT NOT NULL,
        cuisine_type TEXT NOT NULL,
        rating REAL DEFAULT 4.5,
        is_approved INTEGER DEFAULT 0,
        is_open INTEGER DEFAULT 1,
        delivery_time TEXT DEFAULT '30 mins',
        image_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        price REAL NOT NULL,
        description TEXT,
        is_available INTEGER DEFAULT 1,
        is_vegetarian INTEGER DEFAULT 0,
        is_spicy INTEGER DEFAULT 0,
        image_url TEXT,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        restaurant_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        delivery_address TEXT,
        special_instructions TEXT,
        payment_method TEXT DEFAULT 'cash',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES users(id),
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        restaurant_id INTEGER,
        comment TEXT,
        rating REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    );

    CREATE TABLE IF NOT EXISTS blockchain_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        previous_hash TEXT,
        current_hash TEXT,
        block_data TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """


def ensure_schema_updates(cursor):
    """Handle lightweight schema migrations for SQLite."""
    try:
        # Check and update menu_items table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='menu_items'
        """)
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(menu_items)")
            rows = cursor.fetchall()
            # Handle both Row objects and tuples
            if rows and isinstance(rows[0], sqlite3.Row):
                columns = {row['name'] for row in rows}
            else:
                columns = {row[1] for row in rows}
            
            if 'description' not in columns:
                try:
                    cursor.execute("ALTER TABLE menu_items ADD COLUMN description TEXT")
                except sqlite3.Error:
                    pass
            
            if 'is_vegetarian' not in columns:
                try:
                    cursor.execute("ALTER TABLE menu_items ADD COLUMN is_vegetarian INTEGER DEFAULT 0")
                except sqlite3.Error:
                    pass
            
            if 'is_spicy' not in columns:
                try:
                    cursor.execute("ALTER TABLE menu_items ADD COLUMN is_spicy INTEGER DEFAULT 0")
                except sqlite3.Error:
                    pass
        
        # Check if reviews table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reviews'
        """)
        if cursor.fetchone():
            # Get existing columns
            cursor.execute("PRAGMA table_info(reviews)")
            columns = {row['name']: row for row in cursor.fetchall()}
            
            # Add restaurant_id if missing
            if 'restaurant_id' not in columns:
                try:
                    cursor.execute("ALTER TABLE reviews ADD COLUMN restaurant_id INTEGER")
                except sqlite3.Error:
                    pass  # Column might have been added concurrently
            
            # Add created_at if missing (without default - SQLite limitation with ALTER TABLE)
            # Note: CREATE TABLE can use DEFAULT CURRENT_TIMESTAMP, but ALTER TABLE cannot
            if 'created_at' not in columns:
                try:
                    cursor.execute("ALTER TABLE reviews ADD COLUMN created_at TEXT")
                    # Update existing NULL values to current timestamp
                    cursor.execute("UPDATE reviews SET created_at = datetime('now') WHERE created_at IS NULL")
                except sqlite3.Error:
                    pass  # Column might have been added concurrently
        
        # Check if orders table exists and add payment_method if missing
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='orders'
        """)
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(orders)")
            columns = {row['name']: row for row in cursor.fetchall()}
            
            if 'payment_method' not in columns:
                try:
                    cursor.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'cash'")
                except sqlite3.Error:
                    pass  # Column might have been added concurrently
                
    except sqlite3.Error as e:
        # Ignore errors - table might not exist or columns might already exist
        pass


def seed_sample_data(cursor):
    cursor.execute("SELECT COUNT(*) AS count FROM restaurants")
    if cursor.fetchone()['count'] > 0:
        return

    restaurants = [
        (None, 'Dark Knight Diner', 'Burger', 4.8, 1, 1, '25 mins', None),
        (None, 'Villainous Vegan', 'Vegan', 4.4, 1, 1, '30 mins', None),
        (None, 'Sinister Sushi', 'Asian', 4.6, 1, 1, '35 mins', None)
    ]
    cursor.executemany("""
        INSERT INTO restaurants (owner_id, name, cuisine_type, rating, is_approved, is_open, delivery_time, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, restaurants)

    cursor.execute("SELECT id, name FROM restaurants")
    restaurant_lookup = {row['name']: row['id'] for row in cursor.fetchall()}

    menu_items = [
        (restaurant_lookup['Dark Knight Diner'], 'Dark Knight Burger', 'Main', 14.99, 1),
        (restaurant_lookup['Dark Knight Diner'], 'Gotham Fries', 'Side', 4.99, 1),
        (restaurant_lookup['Villainous Vegan'], 'Evil Kale Bowl', 'Main', 12.50, 1),
        (restaurant_lookup['Sinister Sushi'], 'Shadow Dragon Roll', 'Main', 16.75, 1)
    ]
    cursor.executemany("""
        INSERT INTO menu_items (restaurant_id, name, category, price, is_available)
        VALUES (?, ?, ?, ?, ?)
    """, menu_items)