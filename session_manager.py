import json
import logging
from enum import Enum
from typing import Dict, Optional, List
from database import Database

class ConversationState(Enum):
    """Enum for conversation states during the listing process"""
    IDLE = "idle"
    CATEGORY_SELECTION = "category_selection"
    SUBCATEGORY_SELECTION = "subcategory_selection"
    PRODUCT_INPUT = "product_input"
    PROCESSING_PRODUCT = "processing_product"
    CONFIRMATION = "confirmation"
    PRICE_INPUT = "price_input"
    COMPLETED = "completed"

class SessionManager:
    def __init__(self, database: Database):
        self.db = database
        self.categories_cache = None
    
    def load_categories(self, categories_file: str = "shop_categories.json") -> Dict:
        """Load categories from JSON file"""
        if self.categories_cache is None:
            try:
                with open(categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories_cache = data.get('shop_categories', [])
                    logging.info(f"Loaded {len(self.categories_cache)} categories")
            except Exception as e:
                logging.error(f"Error loading categories: {e}")
                self.categories_cache = []
        
        return self.categories_cache
    
    def get_categories_list(self) -> List[Dict]:
        """Get list of all categories"""
        categories = self.load_categories()
        return [{"name": cat["category"], "subcategories": cat["subcategories"]} for cat in categories]
    
    def get_category_by_name(self, category_name: str) -> Optional[Dict]:
        """Get category details by name"""
        categories = self.load_categories()
        for cat in categories:
            if cat["category"].lower() == category_name.lower():
                return cat
        return None
    
    def get_subcategory_by_name(self, category_name: str, subcategory_name: str) -> Optional[Dict]:
        """Get subcategory details by name"""
        category = self.get_category_by_name(category_name)
        if category:
            for subcat in category["subcategories"]:
                if subcat["name"].lower() == subcategory_name.lower():
                    return subcat
        return None
    
    def get_expected_attributes(self, category_name: str, subcategory_name: str) -> List[str]:
        """Get expected attributes for a category/subcategory combination"""
        subcategory = self.get_subcategory_by_name(category_name, subcategory_name)
        if subcategory:
            return subcategory.get("attributes", [])
        return []
    
    def start_listing_session(self, user_id: int) -> bool:
        """Start a new listing session for a user"""
        try:
            # Clear any existing session
            self.db.clear_user_session(user_id)
            
            # Create new session
            self.db.update_user_session(
                user_id=user_id,
                state=ConversationState.CATEGORY_SELECTION.value
            )
            
            # Log the action
            self.db.log_user_action(user_id, "listing_started")
            
            logging.info(f"Started listing session for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error starting listing session: {e}")
            return False
    
    def update_session_state(self, user_id: int, state: ConversationState, **kwargs) -> bool:
        """Update user session state"""
        try:
            update_data = {"state": state.value}
            update_data.update(kwargs)
            
            self.db.update_user_session(user_id=user_id, **update_data)
            
            logging.info(f"Updated session state for user {user_id} to {state.value}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating session state: {e}")
            return False
    
    def get_session_state(self, user_id: int) -> Optional[Dict]:
        """Get current session state for a user"""
        return self.db.get_user_session(user_id)
    
    def set_category(self, user_id: int, category: str) -> bool:
        """Set selected category for user session"""
        try:
            # Validate category exists
            if not self.get_category_by_name(category):
                logging.error(f"Invalid category: {category}")
                return False
            
            self.db.update_user_session(
                user_id=user_id,
                category=category,
                state=ConversationState.SUBCATEGORY_SELECTION.value
            )
            
            # Log the action
            self.db.log_user_action(user_id, "category_selected", {"category": category})
            
            logging.info(f"Set category {category} for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting category: {e}")
            return False
    
    def set_subcategory(self, user_id: int, subcategory: str) -> bool:
        """Set selected subcategory for user session"""
        try:
            session = self.get_session_state(user_id)
            if not session or not session.get('category'):
                logging.error(f"No category selected for user {user_id}")
                return False
            
            # Validate subcategory exists for the selected category
            if not self.get_subcategory_by_name(session['category'], subcategory):
                logging.error(f"Invalid subcategory {subcategory} for category {session['category']}")
                return False
            
            self.db.update_user_session(
                user_id=user_id,
                subcategory=subcategory,
                state=ConversationState.PRODUCT_INPUT.value
            )
            
            # Log the action
            self.db.log_user_action(user_id, "subcategory_selected", {
                "category": session['category'],
                "subcategory": subcategory
            })
            
            logging.info(f"Set subcategory {subcategory} for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting subcategory: {e}")
            return False
    
    def set_product_name(self, user_id: int, product_name: str) -> bool:
        """Set product name for user session"""
        try:
            self.db.update_user_session(
                user_id=user_id,
                product_name=product_name,
                state=ConversationState.PROCESSING_PRODUCT.value
            )
            
            # Log the action
            self.db.log_user_action(user_id, "product_name_entered", {
                "product_name": product_name
            })
            
            logging.info(f"Set product name '{product_name}' for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting product name: {e}")
            return False
    
    def set_extracted_data(self, user_id: int, extracted_data: Dict) -> bool:
        """Set extracted product data for user session"""
        try:
            self.db.update_user_session(
                user_id=user_id,
                extracted_data=extracted_data,
                state=ConversationState.CONFIRMATION.value
            )
            
            # Log the action
            self.db.log_user_action(user_id, "product_data_extracted", {
                "success": extracted_data.get('success', False),
                "confidence": extracted_data.get('confidence', 0),
                "attributes_count": len(extracted_data.get('attributes', {}))
            })
            
            logging.info(f"Set extracted data for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting extracted data: {e}")
            return False
    
    def complete_listing(self, user_id: int, username: str, price: float) -> Optional[int]:
        """Complete the listing and save to database"""
        try:
            session = self.get_session_state(user_id)
            if not session:
                logging.error(f"No session found for user {user_id}")
                return None
            
            extracted_data = session.get('extracted_data')
            if not extracted_data:
                logging.error(f"No extracted data found for user {user_id}")
                return None
            
            # Save product to database
            product_id = self.db.save_product(
                user_id=user_id,
                username=username,
                category=session['category'],
                subcategory=session['subcategory'],
                product_name=session['product_name'],
                attributes=extracted_data.get('attributes', {}),
                price=price
            )
            
            if product_id:
                # Clear the session
                self.db.clear_user_session(user_id)
                
                # Log completion
                self.db.log_user_action(user_id, "listing_completed", {
                    "product_id": product_id,
                    "category": session['category'],
                    "subcategory": session['subcategory'],
                    "product_name": session['product_name'],
                    "price": price
                })
                
                logging.info(f"Completed listing for user {user_id}, product ID: {product_id}")
                return product_id
            
            return None
            
        except Exception as e:
            logging.error(f"Error completing listing: {e}")
            return None
    
    def cancel_listing(self, user_id: int) -> bool:
        """Cancel current listing session"""
        try:
            session = self.get_session_state(user_id)
            if session:
                self.db.log_user_action(user_id, "listing_cancelled", {
                    "state": session.get('state'),
                    "category": session.get('category'),
                    "subcategory": session.get('subcategory'),
                    "product_name": session.get('product_name')
                })
            
            self.db.clear_user_session(user_id)
            logging.info(f"Cancelled listing for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error cancelling listing: {e}")
            return False
    
    def get_session_summary(self, user_id: int) -> Optional[str]:
        """Get a human-readable summary of the current session"""
        session = self.get_session_state(user_id)
        if not session:
            return None
        
        state = session.get('state', 'unknown')
        category = session.get('category', 'Not selected')
        subcategory = session.get('subcategory', 'Not selected')
        product_name = session.get('product_name', 'Not entered')
        
        summary = f"""
📋 **Current Listing Session**
📁 Category: {category}
📂 Subcategory: {subcategory}
🏷️ Product: {product_name}
🔄 Status: {state.replace('_', ' ').title()}
"""
        
        if session.get('extracted_data'):
            extracted = session['extracted_data']
            confidence = extracted.get('confidence', 0)
            summary += f"🎯 Data Confidence: {confidence * 100:.0f}%\n"
        
        return summary.strip()
    
    def is_session_active(self, user_id: int) -> bool:
        """Check if user has an active listing session"""
        session = self.get_session_state(user_id)
        return session is not None and session.get('state') != ConversationState.IDLE.value