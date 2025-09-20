import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class JSONStorage:
    def __init__(self, users_file="users.json", listings_dir="listings"):
        self.users_file = users_file
        self.listings_dir = listings_dir
        self.init_storage()
    
    def init_storage(self):
        """Initialize JSON storage structure"""
        try:
            # Create listings directory if it doesn't exist
            if not os.path.exists(self.listings_dir):
                os.makedirs(self.listings_dir)
            
            # Initialize users.json if it doesn't exist
            if not os.path.exists(self.users_file):
                initial_data = {
                    "sessions": {},
                    "logs": []
                }
                with open(self.users_file, 'w') as f:
                    json.dump(initial_data, f, indent=2)
            
            logging.info("JSON storage initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing JSON storage: {e}")
    
    def _load_users_data(self) -> Dict:
        """Load users data from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading users data: {e}")
            return {"sessions": {}, "logs": []}
    
    def _save_users_data(self, data: Dict):
        """Save users data to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving users data: {e}")
    
    def save_product(self, user_id: int, username: str, category: str, subcategory: str, 
                    product_name: str, attributes: Dict, price: float) -> Optional[int]:
        """Save a product listing to the listings directory"""
        try:
            # Generate product ID based on timestamp
            product_id = int(datetime.now().timestamp() * 1000)  # milliseconds
            
            # Create product data
            product_data = {
                "id": product_id,
                "user_id": user_id,
                "username": username,
                "category": category,
                "subcategory": subcategory,
                "product_name": product_name,
                "attributes": attributes,
                "price": price,
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to listings directory
            listing_file = os.path.join(self.listings_dir, f"listing_{product_id}.json")
            with open(listing_file, 'w') as f:
                json.dump(product_data, f, indent=2)
            
            logging.info(f"Product saved successfully with ID: {product_id}")
            return product_id
            
        except Exception as e:
            logging.error(f"Error saving product: {e}")
            return None
    
    def get_user_session(self, user_id: int) -> Optional[Dict]:
        """Get current user session state"""
        try:
            data = self._load_users_data()
            user_id_str = str(user_id)
            
            if user_id_str in data["sessions"]:
                session = data["sessions"][user_id_str]
                # Convert extracted_data back from string if needed
                if "extracted_data" in session and isinstance(session["extracted_data"], str):
                    try:
                        session["extracted_data"] = json.loads(session["extracted_data"])
                    except:
                        session["extracted_data"] = None
                return session
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting user session: {e}")
            return None
    
    def update_user_session(self, user_id: int, state: str = None, category: str = None, 
                          subcategory: str = None, product_name: str = None, 
                          extracted_data: Dict = None):
        """Update or create user session"""
        try:
            data = self._load_users_data()
            user_id_str = str(user_id)
            
            # Get existing session or create new one
            if user_id_str not in data["sessions"]:
                data["sessions"][user_id_str] = {}
            
            session = data["sessions"][user_id_str]
            
            # Update fields if provided
            if state is not None:
                session["state"] = state
            if category is not None:
                session["category"] = category
            if subcategory is not None:
                session["subcategory"] = subcategory
            if product_name is not None:
                session["product_name"] = product_name
            if extracted_data is not None:
                session["extracted_data"] = extracted_data
            
            session["updated_at"] = datetime.now().isoformat()
            
            self._save_users_data(data)
            
        except Exception as e:
            logging.error(f"Error updating user session: {e}")
    
    def clear_user_session(self, user_id: int):
        """Clear user session after completing the listing"""
        try:
            data = self._load_users_data()
            user_id_str = str(user_id)
            
            if user_id_str in data["sessions"]:
                del data["sessions"][user_id_str]
                self._save_users_data(data)
            
        except Exception as e:
            logging.error(f"Error clearing user session: {e}")
    
    def log_user_action(self, user_id: int, action: str, details: Dict = None):
        """Log user actions for analytics and debugging"""
        try:
            data = self._load_users_data()
            
            log_entry = {
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
            
            data["logs"].append(log_entry)
            
            # Keep only last 1000 logs to prevent file from growing too large
            if len(data["logs"]) > 1000:
                data["logs"] = data["logs"][-1000:]
            
            self._save_users_data(data)
            
        except Exception as e:
            logging.error(f"Error logging user action: {e}")
    
    def get_user_products(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's recent products"""
        try:
            products = []
            
            # List all listing files
            if not os.path.exists(self.listings_dir):
                return products
            
            listing_files = [f for f in os.listdir(self.listings_dir) if f.startswith("listing_") and f.endswith(".json")]
            
            # Load and filter user's products
            for filename in listing_files:
                try:
                    filepath = os.path.join(self.listings_dir, filename)
                    with open(filepath, 'r') as f:
                        product = json.load(f)
                    
                    if product.get("user_id") == user_id:
                        products.append(product)
                except Exception as e:
                    logging.error(f"Error loading listing file {filename}: {e}")
                    continue
            
            # Sort by created_at (most recent first) and limit
            products.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return products[:limit]
            
        except Exception as e:
            logging.error(f"Error getting user products: {e}")
            return []
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get a specific product by ID"""
        try:
            listing_file = os.path.join(self.listings_dir, f"listing_{product_id}.json")
            if os.path.exists(listing_file):
                with open(listing_file, 'r') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            logging.error(f"Error getting product by ID: {e}")
            return None
    
    def update_product_status(self, product_id: int, status: str) -> bool:
        """Update product status"""
        try:
            listing_file = os.path.join(self.listings_dir, f"listing_{product_id}.json")
            if os.path.exists(listing_file):
                with open(listing_file, 'r') as f:
                    product = json.load(f)
                
                product["status"] = status
                product["updated_at"] = datetime.now().isoformat()
                
                with open(listing_file, 'w') as f:
                    json.dump(product, f, indent=2)
                
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error updating product status: {e}")
            return False