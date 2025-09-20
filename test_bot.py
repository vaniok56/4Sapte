#!/usr/bin/env python3
"""
Test script for the Second-Hand Market Bot
Tests all major components without running the full bot
"""

import sys
import asyncio
import logging
from database import Database
from deepseek_api import DeepSeekAPI
from session_manager import SessionManager, ConversationState

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_database():
    """Test database functionality"""
    print("🧪 Testing Database...")
    db = Database("test_secondhand_market.db")
    
    # Test session management
    test_user_id = 12345
    db.update_user_session(test_user_id, state=ConversationState.CATEGORY_SELECTION.value)
    session = db.get_user_session(test_user_id)
    assert session is not None
    assert session['state'] == ConversationState.CATEGORY_SELECTION.value
    
    # Test logging
    db.log_user_action(test_user_id, "test_action", {"test": "data"})
    
    # Test product saving
    product_id = db.save_product(
        user_id=test_user_id,
        username="test_user",
        category="Electronics",
        subcategory="Smartphones & Accessories",
        product_name="iPhone 13 Pro",
        attributes={"Brand": "Apple", "Storage": "128GB"},
        price=799.99
    )
    
    assert product_id is not None
    
    # Test retrieving user products
    products = db.get_user_products(test_user_id)
    assert len(products) > 0
    assert products[0]['product_name'] == "iPhone 13 Pro"
    
    db.clear_user_session(test_user_id)
    print("✅ Database tests passed!")

async def test_session_manager():
    """Test session manager functionality"""
    print("🧪 Testing Session Manager...")
    db = Database("test_secondhand_market.db")
    sm = SessionManager(db)
    
    # Test category loading
    categories = sm.get_categories_list()
    assert len(categories) > 0
    print(f"📋 Loaded {len(categories)} categories")
    
    # Test category retrieval
    electronics = sm.get_category_by_name("Electronics")
    assert electronics is not None
    assert electronics['category'] == "Electronics"
    
    # Test subcategory retrieval
    smartphones = sm.get_subcategory_by_name("Electronics", "Smartphones & Accessories")
    assert smartphones is not None
    assert "Brand" in smartphones['attributes']
    
    # Test expected attributes
    attrs = sm.get_expected_attributes("Electronics", "Smartphones & Accessories")
    assert len(attrs) > 0
    assert "Brand" in attrs
    
    # Test session flow
    test_user_id = 54321
    assert sm.start_listing_session(test_user_id)
    assert sm.is_session_active(test_user_id)
    
    assert sm.set_category(test_user_id, "Electronics")
    assert sm.set_subcategory(test_user_id, "Smartphones & Accessories")
    assert sm.set_product_name(test_user_id, "iPhone 13 Pro Max")
    
    session = sm.get_session_state(test_user_id)
    assert session['category'] == "Electronics"
    assert session['subcategory'] == "Smartphones & Accessories"
    assert session['product_name'] == "iPhone 13 Pro Max"
    
    summary = sm.get_session_summary(test_user_id)
    assert "iPhone 13 Pro Max" in summary
    
    assert sm.cancel_listing(test_user_id)
    assert not sm.is_session_active(test_user_id)
    
    print("✅ Session Manager tests passed!")

async def test_deepseek_api():
    """Test DeepSeek API functionality (mock test)"""
    print("🧪 Testing DeepSeek API (basic initialization)...")
    
    api = DeepSeekAPI("test_key", "https://api.test.com", "test_model")
    assert api.api_key == "test_key"
    assert api.api_url == "https://api.test.com"
    assert api.model == "test_model"
    
    # Test prompt creation
    prompt = api._create_extraction_prompt(
        "iPhone 13 Pro", 
        "Electronics", 
        "Smartphones & Accessories", 
        ["Brand", "Model", "Storage"]
    )
    assert "iPhone 13 Pro" in prompt
    assert "Brand" in prompt
    
    # Test validation
    test_data = {"Brand": "Apple", "Model": "iPhone 13 Pro", "Storage": "Unknown"}
    validated = api._validate_extracted_data(test_data, ["Brand", "Model", "Storage"])
    assert validated["Brand"] == "Apple"
    assert validated["Storage"] == "Unknown"
    
    # Test confidence calculation
    confidence = api._calculate_confidence({"Brand": "Apple", "Model": "iPhone 13 Pro", "Storage": "Unknown"})
    assert 0 <= confidence <= 1
    
    print("✅ DeepSeek API tests passed!")

async def test_complete_flow():
    """Test a complete listing flow simulation"""
    print("🧪 Testing Complete Flow...")
    
    db = Database("test_secondhand_market.db")
    sm = SessionManager(db)
    
    test_user_id = 98765
    username = "test_user_complete"
    
    # Start session
    assert sm.start_listing_session(test_user_id)
    
    # Select category and subcategory
    assert sm.set_category(test_user_id, "Electronics")
    assert sm.set_subcategory(test_user_id, "Smartphones & Accessories")
    
    # Set product name
    assert sm.set_product_name(test_user_id, "Samsung Galaxy S21 Ultra 256GB")
    
    # Simulate extracted data
    mock_extracted_data = {
        'success': True,
        'product_name': 'Samsung Galaxy S21 Ultra 256GB',
        'category': 'Electronics',
        'subcategory': 'Smartphones & Accessories',
        'attributes': {
            'Brand': 'Samsung',
            'Model': 'Galaxy S21 Ultra',
            'Storage Capacity': '256GB',
            'Operating System': 'Android',
            'Screen Size': '6.8 inches',
            'RAM': '12GB',
            'Camera Specs': '108MP Quad Camera',
            'Color': 'Unknown'
        },
        'confidence': 0.85
    }
    
    assert sm.set_extracted_data(test_user_id, mock_extracted_data)
    
    # Complete listing
    product_id = sm.complete_listing(test_user_id, username, 649.99)
    assert product_id is not None
    
    # Verify the listing was saved
    products = db.get_user_products(test_user_id)
    assert len(products) > 0
    saved_product = products[0]
    assert saved_product['product_name'] == 'Samsung Galaxy S21 Ultra 256GB'
    assert saved_product['price'] == 649.99
    assert saved_product['category'] == 'Electronics'
    
    # Verify session was cleared
    assert not sm.is_session_active(test_user_id)
    
    print(f"✅ Complete flow test passed! Product ID: {product_id}")

async def main():
    """Run all tests"""
    print("🚀 Starting Second-Hand Market Bot Tests...\n")
    
    try:
        await test_database()
        print()
        
        await test_session_manager()
        print()
        
        await test_deepseek_api()
        print()
        
        await test_complete_flow()
        print()
        
        print("🎉 All tests passed successfully!")
        print("\n📋 Bot Components Summary:")
        print("   ✅ Database - SQLite with products, sessions, and logs tables")
        print("   ✅ Session Manager - Conversation state tracking and category handling")
        print("   ✅ DeepSeek API - Product attribute extraction (ready for API calls)")
        print("   ✅ Complete Flow - End-to-end listing creation process")
        print("\n🤖 The bot is ready to run with: python script.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)