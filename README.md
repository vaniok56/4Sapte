# Second-Hand Market Telegram Bot

A comprehensive Telegram bot built with Telethon for managing second-hand product listings. The bot uses AI (DeepSeek API) to automatically extract product attributes and saves listings to a SQLite database.

## Features

🤖 **AI-Powered Product Analysis**
- Automatically extracts product attributes using DeepSeek API
- Smart categorization and subcategorization
- Confidence scoring for extracted data

🗃️ **Database Management**
- SQLite database for storing listings
- User session management
- Action logging for analytics

📱 **Interactive Telegram Interface**
- Inline keyboard navigation
- Multi-step conversation flow
- Real-time status updates

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot introduction |
| `/plaseaza_anunt` | Start creating a new product listing |
| `/my_listings` | View your recent listings |
| `/status` | Check current listing session status |
| `/cancel` | Cancel current listing session |
| `/help` | Show detailed help information |
| `/time` | Get current time |

## How It Works

1. **Start Listing**: User types `/plaseaza_anunt`
2. **Select Category**: Bot shows inline keyboard with categories (Electronics, Books & Media, Houses & Apartments)
3. **Select Subcategory**: Bot shows relevant subcategories
4. **Enter Product Name**: User types detailed product name/model
5. **AI Analysis**: Bot uses DeepSeek API to extract attributes
6. **Confirmation**: User reviews and confirms extracted information
7. **Set Price**: User enters selling price
8. **Save to Database**: Listing is saved with all details

## Project Structure

```
patrudesapte/
├── script.py              # Main bot application
├── database.py            # Database operations and schema
├── deepseek_api.py        # DeepSeek API integration
├── session_manager.py     # User session and conversation state
├── bot_handlers.py        # Telegram event handlers
├── test_bot.py           # Comprehensive test suite
├── shop_categories.json   # Product categories and attributes
├── config.ini            # Configuration (API keys, tokens)
├── requirements.txt      # Python dependencies
├── secondhand_market.db  # SQLite database (auto-created)
└── bot.log              # Application logs (auto-created)
```

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Edit `config.ini` with your credentials:

```ini
[default]
BOT_TOKEN = your_telegram_bot_token
api_id = your_telegram_api_id
api_hash = your_telegram_api_hash
DEEPSEE_API_KEY = your_deepseek_api_key
DEEPSEE_API_URL = "https://openrouter.ai/api/v1/chat/completions"
```

**Getting the credentials:**
- **Telegram Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram
- **API ID/Hash**: Get from [my.telegram.org](https://my.telegram.org/auth)
- **DeepSeek API Key**: Get from [OpenRouter.ai](https://openrouter.ai/) or DeepSeek directly

### 3. Run Tests
```bash
python test_bot.py
```

### 4. Start Bot
```bash
python script.py
```

## Database Schema

### Products Table
- `id` - Auto-increment primary key
- `user_id` - Telegram user ID
- `username` - Telegram username
- `category` - Product category
- `subcategory` - Product subcategory
- `product_name` - Product name/model
- `attributes` - JSON string of extracted attributes
- `price` - Selling price
- `status` - active/sold/inactive
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### User Sessions Table
- `user_id` - Telegram user ID (primary key)
- `state` - Current conversation state
- `category` - Selected category
- `subcategory` - Selected subcategory
- `product_name` - Entered product name
- `extracted_data` - JSON string of AI-extracted data
- `updated_at` - Last update timestamp

### Listings Log Table
- `id` - Auto-increment primary key
- `user_id` - Telegram user ID
- `action` - Action performed
- `details` - JSON string with action details
- `timestamp` - Action timestamp

## Categories & Attributes

The bot supports the following categories with AI-extracted attributes:

### Electronics
- **Smartphones & Accessories**: Brand, Model, OS, Screen Size, Storage, RAM, Camera, Battery, Connectivity, Color
- **Computers & Laptops**: Brand, Model, Processor, RAM, Storage Type, Screen Size, Graphics, OS, Weight, Battery
- **Gaming**: Platform, Genre, Rating, Multiplayer, Controller, Headset, Monitor Refresh, Resolution
- **Cameras & Drones**: Brand, Model, Sensor Size, Megapixels, Lens Mount, Video Resolution, Flight Time, Range, Gimbal
- **Audio & Video**: Product Type, Brand, Model, Connectivity, Sound Quality, Wattage, Screen Resolution, Smart Features

### Books & Media
- **Fiction**: Author, Genre, Format, Page Count, Series
- **Non-Fiction**: Author, Topic, Format, Page Count
- **Children's Books**: Author, Age Range, Reading Level, Format, Series
- **Movies & TV Shows**: Genre, Format, Run Time, Rating, Actors
- **Music**: Artist, Genre, Format, Release Year, Album Name

### Houses & Apartments
- **Houses**: Location, Price, Bedrooms, Bathrooms, Square Footage, Lot Size, Year Built, Property Type, Features
- **Apartments**: Location, Price, Bedrooms, Bathrooms, Square Footage, Floor Level, Year Built, Amenities, Lease Term

## API Integration

The bot integrates with DeepSeek API for intelligent product attribute extraction:

- **Model**: deepseek/deepseek-r1:free
- **Temperature**: 0.3 (for consistent results)
- **Max Tokens**: 1000
- **Features**: 
  - Attribute extraction based on product names
  - Confidence scoring
  - Price range suggestions
  - Product descriptions

## Error Handling & Logging

- Comprehensive error handling for all operations
- Detailed logging to `bot.log` file
- User-friendly error messages
- Automatic session recovery
- API failure fallback mechanisms

## Usage Examples

### Creating a Smartphone Listing
1. `/plaseaza_anunt`
2. Select "📁 Electronics"
3. Select "📂 Smartphones & Accessories"
4. Type: "iPhone 13 Pro Max 256GB Space Gray"
5. AI extracts: Brand: Apple, Model: iPhone 13 Pro Max, Storage: 256GB, Color: Space Gray, etc.
6. Confirm extracted data
7. Enter price: "899"
8. ✅ Listing created!

### Creating a Book Listing
1. `/plaseaza_anunt`
2. Select "📁 Books & Media"
3. Select "📂 Fiction"
4. Type: "Harry Potter and the Philosopher's Stone by J.K. Rowling"
5. AI extracts: Author: J.K. Rowling, Genre: Fantasy, Series: Harry Potter, etc.
6. Confirm and set price
7. ✅ Listing saved!

## Development & Testing

The project includes a comprehensive test suite (`test_bot.py`) that verifies:
- Database operations
- Session management
- AI API integration
- Complete workflow simulation

Run tests before deployment:
```bash
python test_bot.py
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions:
1. Check the bot logs in `bot.log`
2. Run the test suite to verify setup
3. Ensure all API credentials are correct
4. Check Telegram bot permissions

---

**Happy Selling! 🚀**