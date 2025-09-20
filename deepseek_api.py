import aiohttp
import json
import logging
from typing import Dict, List, Optional

class DeepSeekAPI:
    def __init__(self, api_key: str, api_url: str, model: str = "deepseek/deepseek-chat-v3.1:free"):
        self.api_key = api_key
        self.api_url = api_url.strip('"')  # Remove quotes if present
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://secondhand-market-bot.app",  # Optional referer
            "X-Title": "Second-Hand Market Bot",  # Optional title
        }
    
    async def extract_product_attributes(self, product_name: str, category: str, 
                                       subcategory: str, expected_attributes: List[str]) -> Dict:
        """
        Extract product attributes using DeepSeek API
        """
        try:
            # Create a comprehensive prompt for attribute extraction
            prompt = self._create_extraction_prompt(product_name, category, subcategory, expected_attributes)
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a product information extraction expert. Your job is to analyze product names and extract detailed attributes. Always respond with valid JSON format containing the requested attributes. If you cannot determine an attribute, use 'Unknown' as the value. Be as accurate and detailed as possible based on the product name provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                logging.info(f"Making API request to: {self.api_url}")
                logging.info(f"Using model: {self.model}")
                
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    # Log response details for debugging
                    logging.info(f"API Response Status: {response.status}")
                    logging.info(f"API Response Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                            
                            if not content:
                                logging.error("Empty content received from API")
                                return {
                                    'success': False,
                                    'error': 'Empty response content from API',
                                    'product_name': product_name
                                }
                            
                            # Parse the JSON response
                            try:
                                extracted_data = json.loads(content)
                                
                                # Validate and clean the response
                                validated_data = self._validate_extracted_data(extracted_data, expected_attributes)
                                
                                logging.info(f"Successfully extracted attributes for: {product_name}")
                                return {
                                    'success': True,
                                    'product_name': product_name,
                                    'category': category,
                                    'subcategory': subcategory,
                                    'attributes': validated_data,
                                    'confidence': self._calculate_confidence(validated_data)
                                }
                                
                            except json.JSONDecodeError as e:
                                logging.error(f"Failed to parse JSON response: {e}")
                                logging.error(f"Raw content: {content}")
                                
                                # Try to extract attributes manually if JSON parsing fails
                                manual_extraction = self._manual_attribute_extraction(content, expected_attributes)
                                return {
                                    'success': True,
                                    'product_name': product_name,
                                    'category': category,
                                    'subcategory': subcategory,
                                    'attributes': manual_extraction,
                                    'confidence': 0.5,
                                    'note': 'Extracted using fallback method due to JSON parsing error'
                                }
                        
                        except aiohttp.ContentTypeError as e:
                            error_text = await response.text()
                            logging.error(f"API returned non-JSON response: {e}")
                            logging.error(f"Response text: {error_text[:500]}...")
                            return {
                                'success': False,
                                'error': f"API returned HTML instead of JSON. Status: {response.status}. Response: {error_text[:200]}...",
                                'product_name': product_name
                            }
                    
                    else:
                        error_text = await response.text()
                        logging.error(f"API request failed with status {response.status}")
                        logging.error(f"Error response: {error_text[:500]}...")
                        return {
                            'success': False,
                            'error': f"API request failed: Status {response.status}. Response: {error_text[:200]}...",
                            'product_name': product_name
                        }
        
        except Exception as e:
            logging.error(f"Error extracting product attributes: {e}")
            return {
                'success': False,
                'error': str(e),
                'product_name': product_name
            }
    
    def _create_extraction_prompt(self, product_name: str, category: str, 
                                subcategory: str, expected_attributes: List[str]) -> str:
        """Create a detailed prompt for attribute extraction"""
        
        attributes_list = '", "'.join(expected_attributes)
        
        prompt = f"""
Please analyze the following product and extract its attributes in JSON format.

Product Name: "{product_name}"
Category: {category}
Subcategory: {subcategory}

Required attributes to extract: ["{attributes_list}"]

Instructions:
1. Based on the product name, determine as many of the required attributes as possible
2. Use your knowledge about typical products in this category to fill in likely attributes
3. For attributes you cannot determine from the product name, use "Unknown"
4. Be specific and detailed when possible
5. Return ONLY a valid JSON object with the attributes as keys

Example format:
{{
    "Brand": "Samsung",
    "Model": "Galaxy S21",
    "Operating System": "Android",
    "Screen Size": "6.2 inches",
    "Storage Capacity": "128GB",
    "RAM": "8GB",
    "Camera Specs": "64MP Triple Camera",
    "Battery Life": "4000mAh",
    "Connectivity (5G, Wi-Fi)": "5G, Wi-Fi 6",
    "Color": "Unknown"
}}

Now extract attributes for the product "{product_name}":
"""
        return prompt
    
    def _validate_extracted_data(self, data: Dict, expected_attributes: List[str]) -> Dict:
        """Validate and clean extracted data"""
        validated = {}
        
        for attr in expected_attributes:
            if attr in data:
                value = data[attr]
                # Clean the value
                if isinstance(value, str):
                    value = value.strip()
                    if value.lower() in ['', 'n/a', 'not available', 'none']:
                        value = 'Unknown'
                validated[attr] = value
            else:
                validated[attr] = 'Unknown'
        
        # Add any additional attributes that were extracted
        for key, value in data.items():
            if key not in validated:
                if isinstance(value, str):
                    value = value.strip()
                validated[key] = value
        
        return validated
    
    def _calculate_confidence(self, attributes: Dict) -> float:
        """Calculate confidence score based on how many attributes were found"""
        total_attrs = len(attributes)
        unknown_attrs = sum(1 for v in attributes.values() if str(v).lower() in ['unknown', 'n/a', ''])
        
        if total_attrs == 0:
            return 0.0
        
        confidence = (total_attrs - unknown_attrs) / total_attrs
        return round(confidence, 2)
    
    def _manual_attribute_extraction(self, content: str, expected_attributes: List[str]) -> Dict:
        """Fallback method to extract attributes if JSON parsing fails"""
        attributes = {}
        
        for attr in expected_attributes:
            # Simple pattern matching to find attributes in text
            lines = content.split('\n')
            for line in lines:
                if attr.lower() in line.lower():
                    # Try to extract value after colon
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        # Clean quotes and common prefixes
                        value = value.strip('"\'')
                        attributes[attr] = value
                        break
            
            # If not found, set as Unknown
            if attr not in attributes:
                attributes[attr] = 'Unknown'
        
        return attributes
    
    async def generate_product_description(self, product_name: str, attributes: Dict) -> str:
        """Generate a nice product description based on attributes"""
        try:
            # Create prompt for description generation
            attrs_text = '\n'.join([f"- {k}: {v}" for k, v in attributes.items() if v != 'Unknown'])
            
            prompt = f"""
Create a concise, appealing product description for a second-hand marketplace listing.

Product: {product_name}
Attributes:
{attrs_text}

Generate a brief description (2-3 sentences) that would appeal to potential buyers. Focus on key features and benefits. Keep it professional and engaging.
"""
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional copywriter specializing in second-hand marketplace listings. Create appealing, honest descriptions that highlight key features."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.5,
                "max_tokens": 200,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        description = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                        return description
                    else:
                        return f"Quality {product_name} available for sale. Contact for more details."
        
        except Exception as e:
            logging.error(f"Error generating description: {e}")
            return f"Quality {product_name} available for sale. Contact for more details."
    
    async def suggest_price_range(self, product_name: str, attributes: Dict, category: str) -> Dict:
        """Suggest price range for the product (optional feature)"""
        try:
            attrs_text = '\n'.join([f"- {k}: {v}" for k, v in attributes.items() if v != 'Unknown'])
            
            prompt = f"""
Based on the following product information, suggest a reasonable price range for a second-hand/used item:

Product: {product_name}
Category: {category}
Attributes:
{attrs_text}

Consider:
1. This is for the second-hand market (used items)
2. Typical depreciation for this type of product
3. Current market conditions
4. Product condition assumed to be "good"

Respond with ONLY a JSON object containing:
{{
    "min_price": <number>,
    "max_price": <number>,
    "currency": "USD",
    "reasoning": "Brief explanation"
}}
"""
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a second-hand market pricing expert. Provide realistic price ranges for used items based on their specifications and market conditions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 200,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        try:
                            price_data = json.loads(content)
                            return price_data
                        except json.JSONDecodeError:
                            return {
                                "min_price": 0,
                                "max_price": 0,
                                "currency": "USD",
                                "reasoning": "Unable to determine price range"
                            }
                    
        except Exception as e:
            logging.error(f"Error suggesting price range: {e}")
            
        return {
            "min_price": 0,
            "max_price": 0,
            "currency": "USD",
            "reasoning": "Unable to determine price range"
        }