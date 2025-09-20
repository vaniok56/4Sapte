"""
Fallback mock data for when the DeepSeek API is not available
This allows the bot to function for testing purposes
"""

import json
import logging
from typing import Dict, List

class MockDeepSeekAPI:
    """Mock DeepSeek API for testing when real API is unavailable"""
    
    def __init__(self, api_key: str, api_url: str, model: str = "mock"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        logging.info("🔧 Using Mock DeepSeek API for testing")
    
    async def extract_product_attributes(self, product_name: str, category: str, 
                                       subcategory: str, expected_attributes: List[str]) -> Dict:
        """
        Mock product attribute extraction with realistic responses
        """
        logging.info(f"Mock extracting attributes for: {product_name}")
        
        # Create mock data based on product name patterns
        mock_data = self._generate_mock_attributes(product_name, category, subcategory, expected_attributes)
        
        return {
            'success': True,
            'product_name': product_name,
            'category': category,
            'subcategory': subcategory,
            'attributes': mock_data,
            'confidence': self._calculate_mock_confidence(mock_data, product_name),
            'price_suggestion': self._get_mock_price_suggestion(product_name, category, mock_data),
            'listing': self._generate_mock_listing(product_name, category, mock_data)
        }
    
    def _generate_mock_attributes(self, product_name: str, category: str, 
                                subcategory: str, expected_attributes: List[str]) -> Dict:
        """Generate realistic mock attributes based on product name"""
        
        attributes = {}
        product_lower = product_name.lower()
        
        # Audio & Video equipment  
        if "jbl" in product_lower or "speaker" in product_lower or "audio" in subcategory.lower():
            if "flip 4" in product_lower:
                mock_responses = {
                    "Product Type (Headphones, Speakers, TV)": "Speakers",
                    "Brand": "JBL",
                    "Model": "Flip 4",
                    "Connectivity (Bluetooth, Wi-Fi)": "Bluetooth 4.2, 3.5mm aux input",
                    "Sound Quality (Hz, dB)": "65Hz-20kHz, 80dB SPL",
                    "Wattage": "16W RMS",
                    "Screen Resolution (TV)": "_Not found_",
                    "Smart Features": "JBL Connect+, IPX7 waterproof, 12-hour battery"
                }
            elif "sony" in product_lower:
                mock_responses = {
                    "Product Type (Headphones, Speakers, TV)": "Headphones",
                    "Brand": "Sony",
                    "Model": self._extract_model_from_name(product_name, "Sony"),
                    "Connectivity (Bluetooth, Wi-Fi)": "Bluetooth 5.0, 3.5mm jack",
                    "Sound Quality (Hz, dB)": "20Hz-20kHz, 100dB SPL",
                    "Wattage": "_Not found_",
                    "Screen Resolution (TV)": "_Not found_",
                    "Smart Features": "Active Noise Cancellation, Touch Controls"
                }
            else:
                mock_responses = {
                    "Product Type (Headphones, Speakers, TV)": "Speakers",
                    "Brand": "Unknown",
                    "Model": "Unknown",
                    "Connectivity (Bluetooth, Wi-Fi)": "Bluetooth",
                    "Sound Quality (Hz, dB)": "_Not found_",
                    "Wattage": "_Not found_",
                    "Screen Resolution (TV)": "_Not found_",
                    "Smart Features": "_Not found_"
                }
        # Electronics - Smartphones & Accessories
        elif "iphone" in product_lower:
            mock_responses = {
                "Brand": "Apple",
                "Model": self._extract_model_from_name(product_name, "iPhone"),
                "Operating System": "iOS 17" if "15" in product_name or "16" in product_name else "iOS 16",
                "Storage Capacity": self._extract_storage(product_name),
                "Color": self._extract_color(product_name),
                "Screen Size": "6.7 inches" if "Pro Max" in product_name else "6.1 inches",
                "RAM": "8GB" if "Pro" in product_name else "6GB",
                "Camera Specs": "48MP Pro camera system" if "Pro" in product_name else "48MP Main camera",
                "Battery Life": "Up to 29 hours video playback" if "Pro Max" in product_name else "Up to 22 hours",
                "Connectivity (5G, Wi-Fi)": "5G, Wi-Fi 6E, Bluetooth 5.3"
            }
        elif "samsung" in product_lower or "galaxy" in product_lower:
            mock_responses = {
                "Brand": "Samsung",
                "Model": self._extract_model_from_name(product_name, "Galaxy"),
                "Operating System": "Android 14" if "S24" in product_name else "Android 13",
                "Storage Capacity": self._extract_storage(product_name),
                "Color": self._extract_color(product_name),
                "Screen Size": "6.8 inches Dynamic AMOLED 2X" if "Ultra" in product_name else "6.2 inches",
                "RAM": "12GB" if "Ultra" in product_name else "8GB",
                "Camera Specs": "200MP telephoto + 50MP main + 12MP ultrawide" if "Ultra" in product_name else "50MP triple camera",
                "Battery Life": "5000mAh with 45W fast charging",
                "Connectivity (5G, Wi-Fi)": "5G, Wi-Fi 7, Bluetooth 5.3"
            }
        elif "macbook" in product_lower or "laptop" in product_lower:
            mock_responses = {
                "Brand": "Apple" if "macbook" in product_lower else "Unknown",
                "Model": self._extract_model_from_name(product_name, "MacBook"),
                "Processor": "M2 chip" if "macbook" in product_lower else "Intel i7",
                "RAM": self._extract_ram(product_name),
                "Storage Type (SSD/HDD)": "SSD",
                "Screen Size": "13.3 inches",
                "Graphics Card": "Integrated",
                "Operating System": "macOS" if "macbook" in product_lower else "Windows 11",
                "Weight": "1.4 kg",
                "Battery Life": "Up to 18 hours"
            }
        # Books & Media
        elif category == "Books & Media":
            if "harry potter" in product_lower:
                mock_responses = {
                    "Author": "J.K. Rowling",
                    "Genre": "Fantasy",
                    "Format (Hardcover, Paperback)": "Paperback",
                    "Page Count": "352",
                    "Series": "Harry Potter"
                }
            else:
                mock_responses = {
                    "Author": "Unknown",
                    "Genre": "Unknown",
                    "Format (Hardcover, Paperback)": "Paperback",
                    "Page Count": "Unknown",
                    "Series": "Unknown"
                }
        else:
            # Generic fallback
            mock_responses = {attr: "Unknown" for attr in expected_attributes}
            # Try to extract some basic info
            if "brand" in [attr.lower() for attr in expected_attributes]:
                mock_responses["Brand"] = self._guess_brand(product_name)
        
        # Fill in expected attributes
        for attr in expected_attributes:
            if attr in mock_responses:
                attributes[attr] = mock_responses[attr]
            else:
                attributes[attr] = "Unknown"
        
        return attributes
    
    def _extract_model_from_name(self, product_name: str, prefix: str) -> str:
        """Extract model information from product name"""
        words = product_name.split()
        model_parts = []
        found_prefix = False
        
        for word in words:
            if prefix.lower() in word.lower():
                found_prefix = True
                model_parts.append(word)
            elif found_prefix and (word.isdigit() or any(char.isdigit() for char in word)):
                model_parts.append(word)
            elif found_prefix and word.lower() in ['pro', 'max', 'plus', 'mini', 'air']:
                model_parts.append(word)
        
        return ' '.join(model_parts) if model_parts else "Unknown"
    
    def _extract_storage(self, product_name: str) -> str:
        """Extract storage capacity from product name"""
        import re
        storage_match = re.search(r'(\d+)(gb|tb)', product_name.lower())
        if storage_match:
            return f"{storage_match.group(1).upper()}{storage_match.group(2).upper()}"
        return "Unknown"
    
    def _extract_ram(self, product_name: str) -> str:
        """Extract RAM from product name"""
        import re
        # Look for patterns like "8GB RAM" or "16GB"
        ram_match = re.search(r'(\d+)(gb|tb)(?:\s+ram)?', product_name.lower())
        if ram_match and int(ram_match.group(1)) <= 64:  # Reasonable RAM size
            return f"{ram_match.group(1)}GB"
        return "8GB"  # Default
    
    def _extract_color(self, product_name: str) -> str:
        """Extract color from product name"""
        colors = ['black', 'white', 'gray', 'grey', 'silver', 'gold', 'blue', 'red', 'green', 
                 'purple', 'pink', 'yellow', 'space gray', 'midnight', 'starlight']
        
        product_lower = product_name.lower()
        for color in colors:
            if color in product_lower:
                return color.title()
        return "Unknown"
    
    def _guess_brand(self, product_name: str) -> str:
        """Guess brand from product name"""
        brands = ['apple', 'samsung', 'google', 'sony', 'lg', 'nintendo', 'microsoft', 
                 'dell', 'hp', 'lenovo', 'asus', 'acer']
        
        product_lower = product_name.lower()
        for brand in brands:
            if brand in product_lower:
                return brand.title()
        return "Unknown"
    
    def _get_mock_price_suggestion(self, product_name: str, category: str, attributes: Dict) -> Dict:
        """Generate mock price suggestions for integrated extraction"""
        product_lower = product_name.lower()
        
        # Simple price estimation based on product type
        if "iphone" in product_lower:
            if "13" in product_name or "14" in product_name or "15" in product_name:
                return {"min_price": 400, "max_price": 800, "currency": "USD", "reasoning": "Based on iPhone resale values"}
            else:
                return {"min_price": 200, "max_price": 500, "currency": "USD", "reasoning": "Based on older iPhone models"}
        elif "samsung" in product_lower or "galaxy" in product_lower:
            return {"min_price": 300, "max_price": 700, "currency": "USD", "reasoning": "Based on Samsung Galaxy resale market"}
        elif "macbook" in product_lower:
            if "m1" in product_lower or "m2" in product_lower or "m3" in product_lower:
                return {"min_price": 550, "max_price": 700, "currency": "USD", "reasoning": "The M1 MacBook Air retains value well due to strong performance and battery life. Good condition models with 8/256GB typically sell in this range, reflecting moderate depreciation from original $999 price given its age and continued macOS support."}
            else:
                return {"min_price": 400, "max_price": 600, "currency": "USD", "reasoning": "Based on MacBook resale values"}
        elif "jbl" in product_lower:
            if "flip" in product_lower:
                return {"min_price": 40, "max_price": 80, "currency": "USD", "reasoning": "JBL Flip speakers maintain good resale value due to durability and brand reputation"}
            else:
                return {"min_price": 30, "max_price": 150, "currency": "USD", "reasoning": "Based on JBL audio equipment resale market"}
        elif category == "Books & Media":
            return {"min_price": 5, "max_price": 25, "currency": "USD", "reasoning": "Typical used book prices"}
        else:
            return {"min_price": 10, "max_price": 100, "currency": "USD", "reasoning": "General second-hand item estimate"}
    
    def _calculate_mock_confidence(self, attributes: Dict, product_name: str) -> float:
        """Advanced confidence calculation matching the real API"""
        total_attrs = len(attributes)
        not_found_attrs = sum(1 for v in attributes.values() if str(v) in ['_Not found_', 'Unknown', 'N/A', ''])
        
        if total_attrs == 0:
            return 0.0
        
        # Base confidence on found attributes
        found_attrs = total_attrs - not_found_attrs
        base_confidence = found_attrs / total_attrs
        
        # ADVANCED CONFIDENCE BOOSTERS
        confidence_boosters = 0.0
        
        # 1. CRITICAL ATTRIBUTES BONUS (+30%)
        critical_attrs = ['Brand', 'Model', 'Product Type']
        critical_found = 0
        for attr in critical_attrs:
            for k, v in attributes.items():
                if any(crit.lower() in k.lower() for crit in [attr]) and str(v) not in ['_Not found_', 'Unknown', 'N/A', '']:
                    critical_found += 1
                    break
        
        if critical_found >= 3:
            confidence_boosters += 0.30
        elif critical_found >= 2:
            confidence_boosters += 0.20
        elif critical_found >= 1:
            confidence_boosters += 0.10
        
        # 2. TECHNICAL DETAIL BONUS (+20%)
        technical_indicators = ['GB', 'MHz', 'inches', 'W', 'Hz', 'mAh', 'MP', 'dB', 'mm', 'kg']
        detailed_attrs = 0
        for v in attributes.values():
            if any(indicator in str(v) for indicator in technical_indicators):
                detailed_attrs += 1
        
        if detailed_attrs >= 3:
            confidence_boosters += 0.20
        elif detailed_attrs >= 2:
            confidence_boosters += 0.15
        elif detailed_attrs >= 1:
            confidence_boosters += 0.10
        
        # 3. WELL-KNOWN PRODUCT BONUS (+15%)
        product_lower = product_name.lower()
        well_known_brands = ['apple', 'samsung', 'jbl', 'sony', 'microsoft', 'google', 'nike', 'adidas', 'canon', 'nikon']
        if any(brand in product_lower for brand in well_known_brands):
            confidence_boosters += 0.15
        
        # 4. CONSISTENCY BONUS (+10%)
        # Check if Brand appears consistently
        brand_value = None
        for k, v in attributes.items():
            if 'brand' in k.lower() and str(v) not in ['_Not found_', 'Unknown', 'N/A', '']:
                brand_value = str(v).lower()
                break
        
        if brand_value and brand_value in product_lower:
            confidence_boosters += 0.10
        
        # Calculate final confidence
        final_confidence = min(base_confidence + confidence_boosters, 1.0)
        
        # MINIMUM CONFIDENCE GUARANTEE for well-known products
        if critical_found >= 2 and found_attrs >= (total_attrs * 0.6):
            final_confidence = max(final_confidence, 0.90)
        
        return round(final_confidence, 2)
    
    def _generate_mock_listing(self, product_name: str, category: str, attributes: Dict) -> Dict:
        """Generate mock listing title and description"""
        product_lower = product_name.lower()
        
        # Generate title
        if "iphone" in product_lower:
            title = f"Selling {product_name}"
        elif "macbook" in product_lower:
            title = f"MacBook for Sale - {product_name}"
        elif "jbl" in product_lower:
            title = f"JBL Speaker - {product_name}"
        elif "samsung" in product_lower or "galaxy" in product_lower:
            title = f"Samsung Galaxy - {product_name}"
        else:
            # Generic title
            brand = attributes.get('Brand', 'Quality')
            if brand != '_Not found_' and brand != 'Unknown':
                title = f"Selling {brand} {product_name}"
            else:
                title = f"Selling {product_name}"
        
        # Generate description based on product type
        if "iphone" in product_lower or "phone" in product_lower:
            description = "Condition 8/10. Used for about 1.5 years. You can check everything in person before buying. All functions work perfectly. Bargaining is appropriate."
        elif "macbook" in product_lower:
            description = "Condition 8/10. Used for 2 years for work and study. You can check everything in person. Battery health is good. It also has a bypassed MDM lock. Bargaining is appropriate."
        elif "jbl" in product_lower or "speaker" in product_lower:
            description = "Condition 9/10. Used occasionally for parties and home listening. You can test the sound quality in person. Comes with original charging cable. Bargaining is appropriate."
        elif "book" in category.lower():
            description = "Condition 8/10. Read once, no damages or markings. You can inspect the book in person. Price is negotiable."
        else:
            # Generic description
            description = "Condition 8/10. Used with care. You can check everything in person before purchase. All features work as expected. Bargaining is appropriate."
        
        return {
            "title": title,
            "description": description
        }