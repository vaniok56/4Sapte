import aiohttp
import json
import logging
from logs import send_logs
from typing import Dict, List, Optional

class AIModelClient:
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url.strip('"')  # Remove quotes if present
        self.model = model.strip('"')  # Remove quotes if present
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://secondhand-market-bot.app",
            "X-Title": "Second-Hand Market Bot",
        }
    
    async def extract_product_attributes(self, product_name: str, category: str, 
                                       subcategory: str, expected_attributes: List[str]) -> Dict:
        """
        Extract product attributes AND price suggestion using a generic AI model in a single call
        """
        try:
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
                send_logs(f"Making API request to: {self.api_url}", 'info')
                send_logs(f"Using model: {self.model}", 'info')
                
                async with session.post(self.api_url, headers=self.headers, json=payload) as response:
                    send_logs(f"API Response Status: {response.status}", 'info')
                    send_logs(f"API Response Headers: {dict(response.headers)}", 'info')
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                            
                            if not content:
                                send_logs("Empty content received from API", 'error')
                                return {
                                    'success': False,
                                    'error': 'Empty response content from API',
                                    'product_name': product_name
                                }
                            
                            try:
                                raw = content
                                if '```json' in raw:
                                    start = raw.find('```json') + len('```json')
                                    end = raw.find('```', start)
                                    if end != -1:
                                        raw = raw[start:end].strip()
                                else:
                                    first_brace = raw.find('{')
                                    last_brace = raw.rfind('}')
                                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                                        raw = raw[first_brace:last_brace+1]

                                extracted_data = json.loads(raw)
                                attributes = extracted_data.get('attributes', extracted_data)
                                price_suggestion = extracted_data.get('price_suggestion', {})
                                listing = extracted_data.get('listing', {})
                                validated_data = self._validate_extracted_data(attributes, expected_attributes)
                                
                                send_logs(f"Successfully extracted attributes for: {product_name}", 'info')
                                return {
                                    'success': True,
                                    'product_name': product_name,
                                    'category': category,
                                    'subcategory': subcategory,
                                    'attributes': validated_data,
                                    'confidence': self._calculate_confidence(validated_data),
                                    'price_suggestion': price_suggestion,
                                    'listing': listing
                                }
                                
                            except json.JSONDecodeError as e:
                                send_logs(f"Failed to parse JSON response: {e}", 'error')
                                send_logs(f"Raw content: {content}", 'error')
                                try:
                                    manual_extraction = self._manual_attribute_extraction(raw if raw else content, expected_attributes)
                                    return {
                                        'success': True,
                                        'product_name': product_name,
                                        'category': category,
                                        'subcategory': subcategory,
                                        'attributes': manual_extraction,
                                        'confidence': 0.5,
                                        'note': 'Extracted using fallback method due to JSON parsing error'
                                    }
                                except Exception as me:
                                    send_logs(f"Fallback manual extraction also failed: {me}", 'error')
                                    return {
                                        'success': False,
                                        'error': f"JSON parse failed and fallback extraction failed: {e} | {me}",
                                        'product_name': product_name
                                    }
                        except aiohttp.ContentTypeError as e:
                            error_text = await response.text()
                            send_logs(f"API returned non-JSON response: {e}", 'error')
                            send_logs(f"Response text: {error_text[:500]}...", 'error')
                            return {
                                'success': False,
                                'error': f"API returned HTML instead of JSON. Status: {response.status}. Response: {error_text[:200]}...",
                                'product_name': product_name
                            }
                    else:
                        error_text = await response.text()
                        send_logs(f"API request failed with status {response.status}", 'error')
                        send_logs(f"Error response: {error_text[:500]}...", 'error')
                        return {
                            'success': False,
                            'error': f"API request failed: Status {response.status}. Response: {error_text[:200]}...",
                            'product_name': product_name
                        }
        except Exception as e:
            send_logs(f"Error extracting product attributes: {e}", 'error')
            return {
                'success': False,
                'error': str(e),
                'product_name': product_name
            }

    def _create_extraction_prompt(self, product_name: str, category: str, 
                                subcategory: str, expected_attributes: List[str]) -> str:
        attributes_list = '", "'.join(expected_attributes)
        prompt = f"""
You are an expert product analyst with extensive knowledge of global consumer products, technical specifications, and market data. Your task is to extract accurate product attributes with 90%+ confidence.

PRODUCT TO ANALYZE:
Name: "{product_name}"
Category: {category}
Subcategory: {subcategory}

REQUIRED ATTRIBUTES: [{attributes_list}]

...existing code...
"""
        return prompt

    def _validate_extracted_data(self, data: Dict, expected_attributes: List[str]) -> Dict:
        # ...existing code copied from deepseek_api
        validated = {}
        for attr in expected_attributes:
            if attr in data:
                value = data[attr]
                if isinstance(value, str):
                    value = value.strip()
                    if value.lower() in ['', 'n/a', 'not available', 'none', 'unknown']:
                        value = '_Not found_'
                validated[attr] = value
            else:
                validated[attr] = '_Not found_'
        for key, value in data.items():
            if key not in validated:
                if isinstance(value, str):
                    value = value.strip()
                    existing_values = list(validated.values())
                    if value not in existing_values or value == '_Not found_':
                        validated[key] = value
        return validated

    def _calculate_confidence(self, attributes: Dict) -> float:
        # ...existing confidence code copied from deepseek_api
        total_attrs = len(attributes)
        not_found_attrs = sum(1 for v in attributes.values() if str(v) in ['_Not found_', 'Unknown', 'N/A', ''])
        if total_attrs == 0:
            return 0.0
        found_attrs = total_attrs - not_found_attrs
        base_confidence = found_attrs / total_attrs
        confidence_boosters = 0.0
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
        specific_patterns = ['v[0-9]', '[0-9]+GB', '[0-9]+MHz', '[0-9]+"', '[0-9]+W', 'Pro', 'Max', 'Plus']
        specific_count = 0
        for v in attributes.values():
            if any(pattern.replace('[0-9]', '\\d') in str(v) for pattern in specific_patterns):
                specific_count += 1
        if specific_count >= 2:
            confidence_boosters += 0.15
        elif specific_count >= 1:
            confidence_boosters += 0.10
        brand_value = None
        for k, v in attributes.items():
            if 'brand' in k.lower() and str(v) not in ['_Not found_', 'Unknown', 'N/A', '']:
                brand_value = str(v).lower()
                break
        if brand_value:
            consistent_mentions = sum(1 for v in attributes.values() if brand_value in str(v).lower())
            if consistent_mentions >= 2:
                confidence_boosters += 0.10
        completeness_ratio = found_attrs / total_attrs
        if completeness_ratio >= 0.9:
            confidence_boosters += 0.05
        elif completeness_ratio >= 0.8:
            confidence_boosters += 0.03
        final_confidence = min(base_confidence + confidence_boosters, 1.0)
        if critical_found >= 2 and found_attrs >= (total_attrs * 0.6):
            final_confidence = max(final_confidence, 0.90)
        return round(final_confidence, 2)
