#!/usr/bin/env python3
"""
Quick validation script to test the regex pattern fixes
"""

def test_command_matching():
    """Test the lambda function based command matching"""
    
    # Test cases
    test_cases = [
        ('/start', True),
        ('/Start', True),
        ('/START', True),
        ('/plaseaza_anunt', True),
        ('/PLASEAZA_ANUNT', True),
        ('/help', True),
        ('/HELP', True),
        ('/cancel', True),
        ('/CANCEL', True),
        ('/status', True),
        ('/my_listings', True),
        ('/time', True),
        ('hello world', False),
        ('/unknown_command', False),
        ('not a command', False)
    ]
    
    # Define the lambda functions used in the bot
    start_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/start')
    plaseaza_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/plaseaza_anunt')
    help_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/help')
    cancel_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/cancel')
    status_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/status')
    my_listings_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/my_listings')
    time_func = lambda e: e and hasattr(e, 'text') and e.text and e.text.lower().startswith('/time')
    text_func = lambda e: e and hasattr(e, 'text') and e.text and not e.text.startswith('/') and e.text.strip() != ''
    
    # Mock event class
    class MockEvent:
        def __init__(self, text):
            self.text = text
    
    print("🧪 Testing command matching functions...\n")
    
    # Test each command
    commands = {
        '/start': start_func,
        '/plaseaza_anunt': plaseaza_func,
        '/help': help_func,
        '/cancel': cancel_func,
        '/status': status_func,
        '/my_listings': my_listings_func,
        '/time': time_func
    }
    
    all_passed = True
    
    for command, func in commands.items():
        print(f"Testing {command} command:")
        
        # Test exact match
        event = MockEvent(command)
        result = func(event)
        expected = True
        if result != expected:
            print(f"  ❌ FAIL: {command} -> Expected {expected}, got {result}")
            all_passed = False
        else:
            print(f"  ✅ PASS: {command} -> {result}")
        
        # Test uppercase
        event = MockEvent(command.upper())
        result = func(event)
        expected = True
        if result != expected:
            print(f"  ❌ FAIL: {command.upper()} -> Expected {expected}, got {result}")
            all_passed = False
        else:
            print(f"  ✅ PASS: {command.upper()} -> {result}")
        
        # Test with extra text (should still match for starts_with)
        event = MockEvent(command + " extra")
        result = func(event)
        expected = True
        if result != expected:
            print(f"  ❌ FAIL: '{command} extra' -> Expected {expected}, got {result}")
            all_passed = False
        else:
            print(f"  ✅ PASS: '{command} extra' -> {result}")
        
        print()
    
    # Test text handler
    print("Testing text message handler:")
    for text, should_match in [
        ("hello world", True),
        ("this is a regular message", True),
        ("/start", False),  # Commands should not match text handler
        ("", False),  # Empty should not match
        ("   ", False)  # Whitespace only should not match
    ]:
        event = MockEvent(text)
        result = text_func(event)
        if result != should_match:
            print(f"  ❌ FAIL: '{text}' -> Expected {should_match}, got {result}")
            all_passed = False
        else:
            print(f"  ✅ PASS: '{text}' -> {result}")
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    success = test_command_matching()
    exit(0 if success else 1)