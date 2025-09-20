import sqlite3
import json
import logging
from datetime import datetime

class Database:
    def __init__(self, db_path="secondhand_market.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    category TEXT NOT NULL,
                    subcategory TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    attributes TEXT, -- JSON string of product attributes
                    price REAL,
                    status TEXT DEFAULT 'active', -- active, sold, inactive
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create user_sessions table for conversation state management
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    state TEXT, -- category_selection, subcategory_selection, product_input, etc.
                    category TEXT,
                    subcategory TEXT,
                    product_name TEXT,
                    extracted_data TEXT, -- JSON string
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create listings_log table for tracking all interactions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL, -- started, category_selected, product_extracted, etc.
                    details TEXT, -- JSON string with action details
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
    
    def save_product(self, user_id, username, category, subcategory, product_name, attributes, price):
        """Save a product listing to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO products (user_id, username, category, subcategory, product_name, attributes, price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, category, subcategory, product_name, json.dumps(attributes), price))
            
            product_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.info(f"Product saved successfully with ID: {product_id}")
            return product_id
            
        except Exception as e:
            logging.error(f"Error saving product: {e}")
            return None
    
    def get_user_session(self, user_id):
        """Get current user session state"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_sessions WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'state': result[1],
                    'category': result[2],
                    'subcategory': result[3],
                    'product_name': result[4],
                    'extracted_data': json.loads(result[5]) if result[5] else None,
                    'updated_at': result[6]
                }
            return None
            
        except Exception as e:
            logging.error(f"Error getting user session: {e}")
            return None
    
    def update_user_session(self, user_id, state=None, category=None, subcategory=None, 
                          product_name=None, extracted_data=None):
        """Update or create user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute('SELECT user_id FROM user_sessions WHERE user_id = ?', (user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing session
                updates = []
                values = []
                
                if state is not None:
                    updates.append("state = ?")
                    values.append(state)
                if category is not None:
                    updates.append("category = ?")
                    values.append(category)
                if subcategory is not None:
                    updates.append("subcategory = ?")
                    values.append(subcategory)
                if product_name is not None:
                    updates.append("product_name = ?")
                    values.append(product_name)
                if extracted_data is not None:
                    updates.append("extracted_data = ?")
                    values.append(json.dumps(extracted_data))
                
                updates.append("updated_at = ?")
                values.append(datetime.now())
                values.append(user_id)
                
                cursor.execute(f'''
                    UPDATE user_sessions 
                    SET {", ".join(updates)}
                    WHERE user_id = ?
                ''', values)
            else:
                # Create new session
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, state, category, subcategory, product_name, extracted_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, state, category, subcategory, product_name, 
                      json.dumps(extracted_data) if extracted_data else None))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Error updating user session: {e}")
    
    def clear_user_session(self, user_id):
        """Clear user session after completing the listing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Error clearing user session: {e}")
    
    def log_user_action(self, user_id, action, details=None):
        """Log user actions for analytics and debugging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO listings_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, json.dumps(details) if details else None))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Error logging user action: {e}")
    
    def get_user_products(self, user_id, limit=10):
        """Get user's recent products"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM products 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            products = []
            for row in results:
                products.append({
                    'id': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'category': row[3],
                    'subcategory': row[4],
                    'product_name': row[5],
                    'attributes': json.loads(row[6]) if row[6] else {},
                    'price': row[7],
                    'status': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                })
            
            return products
            
        except Exception as e:
            logging.error(f"Error getting user products: {e}")
            return []