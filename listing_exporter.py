"""
JSON export functionality for product listings
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging
from logs import send_logs

class ListingExporter:
    def __init__(self, export_dir: str = "exports"):
        """
        Initialize the listing exporter
        
        Args:
            export_dir: Directory where JSON files will be saved
        """
        self.export_dir = export_dir
        
        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
    def export_listing(self, listing_data: Dict, user_id: int, product_id: Optional[int] = None) -> str:
        """
        Export listing data to a JSON file
        
        Args:
            listing_data: Complete listing data including attributes, title, etc.
            user_id: Telegram user ID
            product_id: Database product ID (if available)
            
        Returns:
            str: Path to the exported JSON file
        """
        try:
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create filename
            product_name = listing_data.get('product_name', 'unknown_product')
            # Clean product name for filename (remove special characters)
            clean_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '_')).rstrip()
            clean_name = clean_name.replace(' ', '_').lower()[:30]  # Limit length
            
            filename = f"listing_{user_id}_{clean_name}_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            # Prepare export data
            export_data = {
                "export_info": {
                    "exported_at": datetime.now().isoformat(),
                    "user_id": user_id,
                    "product_id": product_id,
                    "export_version": "1.0"
                },
                "listing": {
                    "title": listing_data.get('listing', {}).get('title', 'No title'),
                    "product_name": listing_data.get('product_name', 'Unknown'),
                    "category": listing_data.get('category', 'Unknown'),
                    "subcategory": listing_data.get('subcategory', 'Unknown'),
                    "attributes": listing_data.get('attributes', {}),
                    "price_suggestion": listing_data.get('price_suggestion', {}),
                    "confidence": listing_data.get('confidence', 0.0),
                    "final_price": listing_data.get('final_price')  # Will be set when user sets price
                }
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            send_logs(f"Listing exported to: {filepath}", 'info')
            return filepath
            
        except Exception as e:
            send_logs(f"Error exporting listing: {e}", 'error')
            raise e
    
    def update_listing_price(self, filepath: str, final_price: float) -> bool:
        """
        Update an exported listing with the final price
        
        Args:
            filepath: Path to the JSON file
            final_price: Final price set by user
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(filepath):
                send_logs(f"File not found: {filepath}", 'error')
                return False
                
            # Read existing data
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update price and timestamp
            data['listing']['final_price'] = final_price
            data['export_info']['price_updated_at'] = datetime.now().isoformat()
            
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            send_logs(f"Price updated in: {filepath}", 'info')
            return True
            
        except Exception as e:
            send_logs(f"Error updating listing price: {e}", 'error')
            return False
    
    def get_user_exports(self, user_id: int, limit: int = 10) -> list:
        """
        Get list of export files for a specific user
        
        Args:
            user_id: Telegram user ID
            limit: Maximum number of files to return
            
        Returns:
            list: List of file paths for the user
        """
        try:
            user_files = []
            
            # Search for files matching user_id pattern
            for filename in os.listdir(self.export_dir):
                if filename.startswith(f"listing_{user_id}_") and filename.endswith(".json"):
                    filepath = os.path.join(self.export_dir, filename)
                    # Get file creation time
                    created_time = os.path.getctime(filepath)
                    user_files.append((filepath, created_time))
            
            # Sort by creation time (newest first) and limit
            user_files.sort(key=lambda x: x[1], reverse=True)
            return [filepath for filepath, _ in user_files[:limit]]
            
        except Exception as e:
            send_logs(f"Error getting user exports: {e}", 'error')
            return []