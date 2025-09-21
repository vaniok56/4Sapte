# Telethon utility # pip install telethon
from telethon import TelegramClient, events
from telethon.tl.custom import Button

import configparser # Library for reading from a configuration file, # pip install configparser
import datetime # Library that we will need to get the day and time, # pip install datetime
import pytz
import logging
from logs import send_logs

# Import our custom modules
from json_storage import JSONStorage
from ai_api import AIModelClient
from session_manager import SessionManager
from bot_handlers import BotHandlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log')
    ]
)

#### Access credentials
config = configparser.ConfigParser() # Define the method to read the configuration file
config.read('config.ini') # read config.ini file

api_id = config.get('default','api_id') # get the api id
api_hash = config.get('default','api_hash') # get the api hash
BOT_TOKEN = config.get('default','BOT_TOKEN') # get the bot token

AI_API_KEY = config.get('default','AI_API_KEY') # get the AI service API key
AI_API_URL = config.get('default','AI_API_URL') # get the AI service URL
AI_MODEL = config.get('default','AI_MODEL') # get the AI model

moldova_tz = pytz.timezone('Europe/Chisinau')

# Initialize components
storage = JSONStorage()

# Initialize AI Model Client (real API only)
try:
    ai_client = AIModelClient(AI_API_KEY, AI_API_URL.strip('"'), AI_MODEL)
    send_logs("AI Model Client initialized successfully", 'info')
except Exception as e:
    send_logs(f"AI Model Client initialization failed: {e}", 'error')
    raise

session_manager = SessionManager()
bot_handlers = BotHandlers(storage, ai_client, session_manager)

# Create the client and the session called session_master. We start the session as the Bot (using bot_token)
client = TelegramClient('sessions/session_master', api_id, api_hash).start(bot_token=BOT_TOKEN)

# Register all bot handlers
bot_handlers.register_handlers(client)

# Define the /start command
@client.on(events.NewMessage(func=lambda e: e.text and e.text.lower().startswith('/start'))) 
async def start(event):
    sender = await event.get_sender()
    SENDER = sender.id
    username = sender.username or f"User_{SENDER}"
    
    text = f"""
🤖 **Second-Hand Market Bot**

Hello {username}! Welcome to the second-hand marketplace bot.

**Available Commands:**
🏪 /plaseaza_anunt - Create a new product listing
📋 /my_listings - View your recent listings  
📊 /status - Check current listing session status
🚫 /cancel - Cancel current listing session
❓ /help - Show this help message

**How it works:**
1. Use /plaseaza_anunt to start listing a product
2. Select category and subcategory
3. Enter product name/model
4. AI will extract product details automatically
5. Confirm details and set your price
6. Listing gets saved to JSON files!

Ready to start selling? Use /plaseaza_anunt to begin! 🚀
"""
    
    await client.send_message(SENDER, text, parse_mode="Markdown")

# Help command
@client.on(events.NewMessage(func=lambda e: e.text and e.text.lower().startswith('/help')))
async def help_command(event):
    sender = await event.get_sender()
    SENDER = sender.id
    
    help_text = """
🤖 **Second-Hand Market Bot - Help**

**📝 Creating a Listing:**
1. Use /plaseaza_anunt to start
2. Choose your product category
3. Select subcategory  
4. Enter detailed product name/model
5. Review AI-extracted product details
6. Set your selling price
7. Done! Your listing is saved

**💡 Tips for better results:**
• Be specific with product names (e.g., "iPhone 13 Pro Max 256GB Space Gray")
• Include brand, model, and key specifications
• The AI will extract details like storage, color, condition, etc.

**🔧 Commands:**
• /plaseaza_anunt - Start new listing
• /my_listings - View your listings
• /status - Check current progress
• /cancel - Cancel current session
• /help - Show this help

**🎯 Categories Available:**
📱 Electronics (phones, laptops, cameras, etc.)
📚 Books & Media (books, movies, music)
🏠 Houses & Apartments

Need help? The bot will guide you through each step! 🚀
"""
    
    await client.send_message(SENDER, help_text, parse_mode="Markdown")

### MAIN
if __name__ == '__main__':
    send_logs("Second-Hand Market Bot Starting...", 'info')
    send_logs(f"JSON Storage initialized: {storage.users_file} and {storage.listings_dir}/", 'info')
    
    # Check which API is being used
    api_type = f"AI Service - Model: {ai_client.model}"
    send_logs(f"AI Service: {api_type}", 'info')
    
    send_logs(f"Categories loaded: {len(session_manager.get_categories())} categories", 'info')
    
    try:
        client.run_until_disconnected()
    except KeyboardInterrupt:
        send_logs("Bot stopped by user", 'info')
    except Exception as e:
        send_logs(f"Fatal error: {e}", 'error')
