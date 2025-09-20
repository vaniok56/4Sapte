#!/usr/bin/env python3
"""
Test script to verify DeepSeek API integration
"""

import asyncio
import configparser
from deepseek_api import DeepSeekAPI

async def test_deepseek_api():
    """Test the DeepSeek API with a simple request"""
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    api_key = config.get('default', 'DEEPSEE_API_KEY')
    api_url = config.get('default', 'DEEPSEE_API_URL')
    model = "deepseek/deepseek-chat-v3.1:free"
    
    print(f"🧪 Testing DeepSeek API...")
    print(f"📍 API URL: {api_url}")
    print(f"🤖 Model: {model}")
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-10:] if len(api_key) > 30 else api_key}")
    print()
    
    # Initialize API
    deepseek_api = DeepSeekAPI(api_key, api_url, model)
    
    # Test product extraction
    print("🔍 Testing product attribute extraction...")
    result = await deepseek_api.extract_product_attributes(
        product_name="iPhone 13 Pro Max 256GB Space Gray",
        category="Electronics",
        subcategory="Smartphones & Accessories",
        expected_attributes=["Brand", "Model", "Storage Capacity", "Color", "Operating System"]
    )
    
    print("📋 API Response:")
    print(f"Success: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"Product: {result.get('product_name')}")
        print(f"Confidence: {result.get('confidence', 0) * 100:.1f}%")
        print("Attributes:")
        for key, value in result.get('attributes', {}).items():
            print(f"  • {key}: {value}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result.get('success', False)

if __name__ == "__main__":
    success = asyncio.run(test_deepseek_api())
    print(f"\n{'✅ Test passed!' if success else '❌ Test failed!'}")
    exit(0 if success else 1)