#!/usr/bin/env python3
"""
Complete integration test for the bot with API fixes
"""

import asyncio
import configparser
import logging
from database import Database
from deepseek_api import DeepSeekAPI
from mock_deepseek_api import MockDeepSeekAPI
from session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_real_api():
    """Test the real DeepSeek API"""
    print("🧪 Testing Real DeepSeek API...")
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    api_key = config.get('default', 'DEEPSEE_API_KEY')
    api_url = config.get('default', 'DEEPSEE_API_URL')
    model = "deepseek/deepseek-chat-v3.1:free"
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-5:]}")
    print(f"🌐 API URL: {api_url}")
    print(f"🤖 Model: {model}")
    
    try:
        api = DeepSeekAPI(api_key, api_url, model)
        result = await api.extract_product_attributes(
            product_name="iPhone 13 Pro Max 256GB Space Gray",
            category="Electronics", 
            subcategory="Smartphones & Accessories",
            expected_attributes=["Brand", "Model", "Storage Capacity", "Color"]
        )
        
        if result.get('success'):
            print("✅ Real API working!")
            print(f"   Extracted {len(result.get('attributes', {}))} attributes")
            print(f"   Confidence: {result.get('confidence', 0) * 100:.1f}%")
            return True
        else:
            print(f"❌ Real API failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Real API exception: {e}")
        return False

async def test_mock_api():
    """Test the mock API"""
    print("\n🧪 Testing Mock API...")
    
    try:
        api = MockDeepSeekAPI("test", "test", "mock")
        result = await api.extract_product_attributes(
            product_name="iPhone 13 Pro Max 256GB Space Gray",
            category="Electronics",
            subcategory="Smartphones & Accessories", 
            expected_attributes=["Brand", "Model", "Storage Capacity", "Color"]
        )
        
        if result.get('success'):
            print("✅ Mock API working!")
            print(f"   Generated {len(result.get('attributes', {}))} attributes")
            for key, value in result.get('attributes', {}).items():
                print(f"   • {key}: {value}")
            return True
        else:
            print(f"❌ Mock API failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Mock API exception: {e}")
        return False

async def test_complete_flow():
    """Test complete listing flow with fallback"""
    print("\n🧪 Testing Complete Flow...")
    
    # Load config
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    api_key = config.get('default', 'DEEPSEE_API_KEY')
    api_url = config.get('default', 'DEEPSEE_API_URL')
    model = "deepseek/deepseek-chat-v3.1:free"
    
    # Initialize components with fallback
    db = Database("test_integration.db")
    
    try:
        api = DeepSeekAPI(api_key, api_url, model)
        # Test a quick API call to see if it works
        test_result = await api.extract_product_attributes(
            "Test Product", "Electronics", "Test", ["Brand"]
        )
        if not test_result.get('success'):
            raise Exception("API test failed")
        print("✅ Using Real DeepSeek API")
        api_type = "Real"
    except Exception as e:
        print(f"⚠️ Real API failed ({e}), using Mock API")
        api = MockDeepSeekAPI(api_key, api_url, model)
        api_type = "Mock"
    
    sm = SessionManager(db)
    
    # Simulate complete user flow
    user_id = 999999
    username = "test_user"
    
    # Start session
    success = sm.start_listing_session(user_id)
    print(f"📝 Session started: {success}")
    
    # Select category and subcategory
    success = sm.set_category(user_id, "Electronics")
    print(f"📁 Category set: {success}")
    
    success = sm.set_subcategory(user_id, "Smartphones & Accessories") 
    print(f"📂 Subcategory set: {success}")
    
    # Set product name
    success = sm.set_product_name(user_id, "Samsung Galaxy S21 Ultra 256GB Phantom Black")
    print(f"🏷️ Product name set: {success}")
    
    # Extract attributes
    expected_attrs = sm.get_expected_attributes("Electronics", "Smartphones & Accessories")
    result = await api.extract_product_attributes(
        "Samsung Galaxy S21 Ultra 256GB Phantom Black",
        "Electronics", 
        "Smartphones & Accessories",
        expected_attrs
    )
    
    print(f"🔍 Attribute extraction: {result.get('success')}")
    if result.get('success'):
        print(f"   Confidence: {result.get('confidence', 0) * 100:.1f}%")
        print("   Attributes:")
        for key, value in result.get('attributes', {}).items()[:5]:  # Show first 5
            print(f"     • {key}: {value}")
    
    # Save extracted data
    success = sm.set_extracted_data(user_id, result)
    print(f"💾 Data saved to session: {success}")
    
    # Complete listing
    product_id = sm.complete_listing(user_id, username, 649.99)
    print(f"✅ Listing completed: {product_id is not None}")
    
    if product_id:
        print(f"   Product ID: {product_id}")
        
        # Verify it was saved
        products = db.get_user_products(user_id, limit=1)
        if products:
            product = products[0]
            print(f"   Verified in DB: {product['product_name']}")
            print(f"   Price: ${product['price']}")
    
    print(f"\n🎉 Complete flow test using {api_type} API: {'✅ PASSED' if product_id else '❌ FAILED'}")
    return product_id is not None

async def main():
    """Run all integration tests"""
    print("🚀 Starting Integration Tests for Second-Hand Market Bot\n")
    
    # Test real API first
    real_api_works = await test_real_api()
    
    # Test mock API
    mock_api_works = await test_mock_api()
    
    # Test complete flow  
    complete_flow_works = await test_complete_flow()
    
    print(f"\n📊 Test Results:")
    print(f"   Real DeepSeek API: {'✅ WORKING' if real_api_works else '❌ FAILED'}")
    print(f"   Mock API Fallback: {'✅ WORKING' if mock_api_works else '❌ FAILED'}")
    print(f"   Complete Bot Flow: {'✅ WORKING' if complete_flow_works else '❌ FAILED'}")
    
    if complete_flow_works:
        print(f"\n🎉 Bot is ready to run!")
        if not real_api_works:
            print("⚠️  Note: Using Mock API for attribute extraction (Real API unavailable)")
        else:
            print("✅ Real DeepSeek API is working correctly!")
        print("\n🚀 Start the bot with: python script.py")
    else:
        print(f"\n❌ Bot has issues that need to be resolved.")
    
    return complete_flow_works

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)