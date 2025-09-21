import json
import logging
from logs import send_logs
from enum import Enum
from typing import Dict, List, Optional, Any
from json_storage import JSONStorage

class ConversationState(Enum):
    IDLE = "idle"
    CATEGORY_SELECTION = "category_selection"
    SUBCATEGORY_SELECTION = "subcategory_selection"
    PRODUCT_INPUT = "product_input"
    PROCESSING_PRODUCT = "processing_product"
    CONFIRMATION = "confirmation"
    DESCRIPTION_INPUT = "description_input"
    PRICE_INPUT = "price_input"
    COMPLETED = "completed"

class SessionManager:
    def __init__(self, categories_file="shop_categories.json"):
        self.storage = JSONStorage()
        self.categories = self._load_categories(categories_file)
    
    def _load_categories(self, categories_file: str) -> Dict:
        try:
            with open(categories_file, 'r') as f:
                data = json.load(f)
            send_logs(f"Loaded {len(data.get('shop_categories', []))} categories", 'info')
            return data
        except Exception as e:
            send_logs(f"Error loading categories: {e}", 'error')
            return {"shop_categories": []}
    
    def get_categories(self) -> List[Dict]:
        return self.categories.get("shop_categories", [])
    
    def get_category_by_name(self, category_name: str) -> Optional[Dict]:
        categories = self.get_categories()
        for cat in categories:
            if cat["category"].lower() == category_name.lower():
                return cat
        return None
    
    def get_subcategory_by_name(self, category_name: str, subcategory_name: str) -> Optional[Dict]:
        category = self.get_category_by_name(category_name)
        if category:
            for subcat in category["subcategories"]:
                if subcat["name"].lower() == subcategory_name.lower():
                    return subcat
        return None
    
    def get_expected_attributes(self, category_name: str, subcategory_name: str) -> List[str]:
        subcategory = self.get_subcategory_by_name(category_name, subcategory_name)
        if subcategory:
            return subcategory.get("attributes", [])
        return []
    
    def start_new_session(self, user_id: int) -> bool:
        try:
            self.storage.update_user_session(
                user_id=user_id,
                state=ConversationState.CATEGORY_SELECTION.value
            )
            self.storage.log_user_action(user_id, "session_started", {})
            send_logs(f"Started new session for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error starting session: {e}", 'error')
            return False
    
    def get_session_state(self, user_id: int) -> Optional[Dict]:
        return self.storage.get_user_session(user_id)
    
    def update_session_state(self, user_id: int, state: ConversationState, **kwargs) -> bool:
        """Update user session state with additional data"""
        try:
            # Prepare update data
            update_data = {"state": state.value}
            update_data.update(kwargs)
            
            self.storage.update_user_session(user_id=user_id, **update_data)
            
            send_logs(f"Updated session state for user {user_id} to {state.value}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error updating session state: {e}", 'error')
            return False
    
    def set_category(self, user_id: int, category: str) -> bool:
        try:
            if not self.get_category_by_name(category):
                send_logs(f"Invalid category: {category}", 'error')
                return False
            
            self.storage.update_user_session(
                user_id=user_id,
                category=category,
                state=ConversationState.SUBCATEGORY_SELECTION.value
            )
            self.storage.log_user_action(user_id, "category_selected", {"category": category})
            send_logs(f"Set category {category} for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error setting category: {e}", 'error')
            return False
    
    def set_subcategory(self, user_id: int, subcategory: str) -> bool:
        try:
            session = self.get_session_state(user_id)
            if not session or not session.get('category'):
                send_logs(f"No category selected for user {user_id}", 'error')
                return False
            
            if not self.get_subcategory_by_name(session['category'], subcategory):
                send_logs(f"Invalid subcategory {subcategory}", 'error')
                return False
            
            self.storage.update_user_session(
                user_id=user_id,
                subcategory=subcategory,
                state=ConversationState.PRODUCT_INPUT.value
            )
            self.storage.log_user_action(user_id, "subcategory_selected", {
                "category": session['category'],
                "subcategory": subcategory
            })
            send_logs(f"Set subcategory {subcategory} for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error setting subcategory: {e}", 'error')
            return False
    
    def set_product_name(self, user_id: int, product_name: str) -> bool:
        try:
            self.storage.update_user_session(
                user_id=user_id,
                product_name=product_name,
                state=ConversationState.PROCESSING_PRODUCT.value
            )
            self.storage.log_user_action(user_id, "product_name_entered", {
                "product_name": product_name
            })
            send_logs(f"Set product name for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error setting product name: {e}", 'error')
            return False
    
    def set_extracted_data(self, user_id: int, extracted_data: Dict) -> bool:
        try:
            self.storage.update_user_session(
                user_id=user_id,
                extracted_data=extracted_data,
                state=ConversationState.CONFIRMATION.value
            )
            self.storage.log_user_action(user_id, "product_data_extracted", {
                "success": extracted_data.get('success', False),
                "confidence": extracted_data.get('confidence', 0),
                "attributes_count": len(extracted_data.get('attributes', {}))
            })
            send_logs(f"Set extracted data for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error setting extracted data: {e}", 'error')
            return False
    
    def set_description(self, user_id: int, description: str) -> bool:
        """Set user-provided description for the listing"""
        try:
            session = self.get_session_state(user_id)
            if not session:
                send_logs(f"No session found for user {user_id}", 'error')
                return False
            
            # Update the extracted data to include the manual description
            extracted_data = session.get('extracted_data', {})
            if 'listing' not in extracted_data:
                extracted_data['listing'] = {}
            extracted_data['listing']['description'] = description
            
            self.storage.update_user_session(
                user_id=user_id,
                extracted_data=extracted_data,
                state=ConversationState.PRICE_INPUT.value
            )
            
            self.storage.log_user_action(user_id, "description_entered", {
                "description_length": len(description)
            })
            
            send_logs(f"Set description for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error setting description: {e}", 'error')
            return False
    
    def complete_listing(self, user_id: int, username: str, price: float) -> Optional[int]:
        try:
            session = self.get_session_state(user_id)
            if not session:
                send_logs(f"No session found for user {user_id}", 'error')
                return None
            
            extracted_data = session.get('extracted_data')
            if not extracted_data:
                send_logs(f"No extracted data found for user {user_id}", 'error')
                return None
            
            product_id = self.storage.save_product(
                user_id=user_id,
                username=username,
                category=extracted_data.get('category', session.get('category', 'Unknown')),
                subcategory=extracted_data.get('subcategory', session.get('subcategory', 'Unknown')),
                product_name=extracted_data.get('product_name', session.get('product_name', 'Unknown')),
                attributes=extracted_data.get('attributes', {}),
                price=price
            )
            
            if product_id:
                self.storage.clear_user_session(user_id)
                self.storage.log_user_action(user_id, "listing_completed", {
                    "product_id": product_id,
                    "category": extracted_data.get('category', 'Unknown'),
                    "price": price
                })
                send_logs(f"Completed listing for user {user_id}, product ID: {product_id}", 'info')
                return product_id
            
            return None
        except Exception as e:
            send_logs(f"Error completing listing: {e}", 'error')
            return None
    
    def cancel_listing(self, user_id: int) -> bool:
        try:
            session = self.get_session_state(user_id)
            if session:
                self.storage.log_user_action(user_id, "listing_cancelled", {
                    "state": session.get('state'),
                    "category": session.get('category'),
                    "subcategory": session.get('subcategory'),
                    "product_name": session.get('product_name')
                })
            
            self.storage.clear_user_session(user_id)
            send_logs(f"Cancelled listing for user {user_id}", 'info')
            return True
        except Exception as e:
            send_logs(f"Error cancelling listing: {e}", 'error')
            return False
    
    def is_session_active(self, user_id: int) -> bool:
        session = self.get_session_state(user_id)
        return session is not None and session.get('state') != ConversationState.IDLE.value
    
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

    def log_user_action(self, user_id: int, action: str, details: Dict) -> bool:
        """Log user action - delegates to storage"""
        try:
            self.storage.log_user_action(user_id, action, details)
            return True
        except Exception as e:
            send_logs(f"Error logging user action: {e}", 'error')
            return False
