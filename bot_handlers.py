from telethon import events
from telethon.tl.custom import Button
import logging
from typing import List, Dict
from session_manager import SessionManager, ConversationState
from deepseek_api import DeepSeekAPI
from json_storage import JSONStorage
from listing_exporter import ListingExporter
import re

class BotHandlers:
    def __init__(self, storage: JSONStorage, deepseek_api: DeepSeekAPI, session_manager: SessionManager):
        self.storage = storage
        self.deepseek_api = deepseek_api
        self.session_manager = session_manager
        self.exporter = ListingExporter()
    
    async def _get_user_info(self, event):
        """Helper method to get user info from event"""
        sender = await event.get_sender()
        return sender.id, sender.username or f"User_{sender.id}"
    
    def register_handlers(self, client):
        """Register all bot event handlers"""
        
        @client.on(events.NewMessage(func=lambda e: e.text and e.text.lower().startswith('/plaseaza_anunt')))
        async def plaseaza_anunt_command(event):
            await self.handle_plaseaza_anunt(event)
        
        @client.on(events.CallbackQuery())
        async def callback_handler(event):
            await self.handle_callback_query(event)
        
        @client.on(events.NewMessage(func=lambda e: e.text and not e.text.startswith('/') and e.text.strip() != ''))
        async def text_message_handler(event):
            await self.handle_text_message(event)
        
        @client.on(events.NewMessage(func=lambda e: e.text and e.text.lower().startswith('/cancel')))
        async def cancel_command(event):
            await self.handle_cancel_command(event)
        
        @client.on(events.NewMessage(func=lambda e: e.text and e.text.lower().startswith('/status')))
        async def status_command(event):
            await self.handle_status_command(event)
        
        @client.on(events.NewMessage(func=lambda e: e.text and e.text.lower().startswith('/my_listings')))
        async def my_listings_command(event):
            await self.handle_my_listings_command(event)
    
    async def handle_plaseaza_anunt(self, event):
        """Handle the /plaseaza_anunt command"""
        try:
            sender = await event.get_sender()
            user_id = sender.id
            
            # Check if user already has an active session
            if self.session_manager.is_session_active(user_id):
                summary = self.session_manager.get_session_summary(user_id)
                await event.respond(
                    f"❗ You already have an active listing session!\n\n{summary}\n\n"
                    f"Use /cancel to cancel current session or /status to see current progress.",
                    parse_mode="Markdown"
                )
                return
            
            # Start new listing session
            if self.session_manager.start_new_session(user_id):
                await self.show_category_selection(event)
            else:
                await event.respond("❌ Failed to start listing session. Please try again.")
                
        except Exception as e:
            logging.error(f"Error in plaseaza_anunt command: {e}")
            await event.respond("❌ An error occurred. Please try again later.")
    
    async def show_category_selection(self, event):
        """Show category selection inline keyboard"""
        try:
            categories = self.session_manager.get_categories()
            
            if not categories:
                await event.respond("❌ No categories available. Please contact administrator.")
                return
            
            # Create inline keyboard with categories (2 per row)
            buttons = []
            for i in range(0, len(categories), 2):
                row = []
                for j in range(i, min(i + 2, len(categories))):
                    cat_name = categories[j]["category"]
                    row.append(Button.inline(
                        text=f"📁 {cat_name}",
                        data=f"cat_{cat_name}"
                    ))
                buttons.append(row)
            
            # Add cancel button
            buttons.append([Button.inline("❌ Cancel", "cancel_listing")])
            
            await event.respond(
                "🏪 **Create New Listing**\n\n"
                "Please select a category for your product:",
                buttons=buttons,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logging.error(f"Error showing category selection: {e}")
            await event.respond("❌ Error displaying categories. Please try again.")
    
    async def show_subcategory_selection(self, event, category_name: str):
        """Show subcategory selection for the chosen category"""
        try:
            category = self.session_manager.get_category_by_name(category_name)
            if not category:
                await event.respond("❌ Invalid category. Please try again.")
                return
            
            subcategories = category["subcategories"]
            
            # Create inline keyboard with subcategories
            buttons = []
            for subcat in subcategories:
                subcat_name = subcat["name"]
                buttons.append([Button.inline(
                    text=f"📂 {subcat_name}",
                    data=f"subcat_{category_name}_{subcat_name}"
                )])
            
            # Add back and cancel buttons
            buttons.append([
                Button.inline("🔙 Back to Categories", "back_to_categories"),
                Button.inline("❌ Cancel", "cancel_listing")
            ])
            
            await event.edit(
                f"📁 **Category:** {category_name}\n\n"
                f"Please select a subcategory:",
                buttons=buttons,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logging.error(f"Error showing subcategory selection: {e}")
            await event.respond("❌ Error displaying subcategories. Please try again.")
    
    async def handle_callback_query(self, event):
        """Handle inline keyboard button presses"""
        try:
            data = event.data.decode('utf-8')
            sender = await event.get_sender()
            user_id = sender.id
            
            if data.startswith("cat_"):
                # Category selection
                category_name = data[4:]  # Remove "cat_" prefix
                
                if self.session_manager.set_category(user_id, category_name):
                    await self.show_subcategory_selection(event, category_name)
                else:
                    await event.answer("❌ Error selecting category. Please try again.")
            
            elif data.startswith("subcat_"):
                # Subcategory selection
                parts = data[7:].split("_", 1)  # Remove "subcat_" prefix
                if len(parts) == 2:
                    category_name, subcategory_name = parts
                    
                    if self.session_manager.set_subcategory(user_id, subcategory_name):
                        await self.request_product_name(event, category_name, subcategory_name)
                    else:
                        await event.answer("❌ Error selecting subcategory. Please try again.")
            
            elif data == "back_to_categories":
                # Go back to category selection
                session = self.session_manager.get_session_state(user_id)
                if session:
                    self.session_manager.update_session_state(user_id, ConversationState.CATEGORY_SELECTION)
                    await self.show_category_selection(event)
            
            elif data == "cancel_listing":
                # Cancel listing
                await self.cancel_listing(event, user_id)
            
            elif data == "confirm_product":
                # User confirmed the extracted product data, now ask for description
                await self.request_description(event, user_id)
            
            elif data == "reject_product":
                # User rejected the extracted data, ask for product name again
                session = self.session_manager.get_session_state(user_id)
                if session:
                    self.session_manager.update_session_state(user_id, ConversationState.PRODUCT_INPUT)
                    await event.edit(
                        f"📁 **Category:** {session['category']}\n"
                        f"📂 **Subcategory:** {session['subcategory']}\n\n"
                        f"Please enter the product name again (be more specific):",
                        buttons=[[Button.inline("❌ Cancel", "cancel_listing")]],
                        parse_mode="Markdown"
                    )
            
            await event.answer()
            
        except Exception as e:
            logging.error(f"Error handling callback query: {e}")
            await event.answer("❌ An error occurred. Please try again.")
    
    async def request_product_name(self, event, category_name: str, subcategory_name: str):
        """Request product name from user"""
        try:
            await event.edit(
                f"📁 **Category:** {category_name}\n"
                f"📂 **Subcategory:** {subcategory_name}\n\n"
                f"🏷️ Please enter the product name/model:\n"
                f"*(Be as specific as possible, e.g., \"iPhone 13 Pro Max 256GB\")*",
                buttons=[[Button.inline("❌ Cancel", "cancel_listing")]],
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logging.error(f"Error requesting product name: {e}")
    
    async def handle_text_message(self, event):
        """Handle text messages based on current session state"""
        try:
            sender = await event.get_sender()
            user_id = sender.id
            message_text = event.text.strip()
            
            session = self.session_manager.get_session_state(user_id)
            if not session:
                return  # No active session, ignore text message
            
            state = session.get('state')
            
            if state == ConversationState.PRODUCT_INPUT.value:
                await self.process_product_name(event, user_id, message_text)
            
            elif state == ConversationState.DESCRIPTION_INPUT.value:
                await self.process_description_input(event, user_id, message_text)
            
            elif state == ConversationState.PRICE_INPUT.value:
                await self.process_price_input(event, user_id, message_text)
                
        except Exception as e:
            logging.error(f"Error handling text message: {e}")
            await event.respond("❌ An error occurred processing your message.")
    
    async def process_product_name(self, event, user_id: int, product_name: str):
        """Process the product name and extract attributes"""
        try:
            session = self.session_manager.get_session_state(user_id)
            if not session:
                await event.respond("❌ Session not found. Please start over with /plaseaza_anunt")
                return
            
            # Validate product name
            if len(product_name.strip()) < 3:
                await event.respond("❌ Product name too short. Please enter a more detailed product name.")
                return
            
            # Set product name and update state
            if not self.session_manager.set_product_name(user_id, product_name):
                await event.respond("❌ Error saving product name. Please try again.")
                return
            
            # Show processing message
            processing_message = await event.respond(
                f"🔍 **Analyzing product...**\n\n"
                f"📁 Category: {session['category']}\n"
                f"📂 Subcategory: {session['subcategory']}\n"
                f"🏷️ Product: {product_name}\n\n"
                f"⏳ Please wait while I extract product information...",
                parse_mode="Markdown"
            )
            
            # Get expected attributes
            expected_attributes = self.session_manager.get_expected_attributes(
                session['category'], session['subcategory']
            )
            
            # Extract product attributes using DeepSeek API
            extracted_data = await self.deepseek_api.extract_product_attributes(
                product_name=product_name,
                category=session['category'],
                subcategory=session['subcategory'],
                expected_attributes=expected_attributes
            )
            
            # Save extracted data to session
            if self.session_manager.set_extracted_data(user_id, extracted_data):
                await self.show_product_confirmation(processing_message, extracted_data)
            else:
                await processing_message.edit("❌ Error processing product data. Please try again.")
                
        except Exception as e:
            logging.error(f"Error processing product name: {e}")
            await event.respond("❌ Error analyzing product. Please try again.")
    
    async def show_product_confirmation(self, message, extracted_data: Dict):
        """Show extracted product data with complete listing for user confirmation"""
        try:
            if not extracted_data.get('success'):
                await message.edit(
                    f"❌ **Unable to extract product information**\n\n"
                    f"Error: {extracted_data.get('error', 'Unknown error')}\n\n"
                    f"Please try entering a more specific product name.",
                    buttons=[[Button.inline("❌ Cancel", "cancel_listing")]],
                    parse_mode="Markdown"
                )
                return

            attributes = extracted_data.get('attributes', {})
            confidence = extracted_data.get('confidence', 0)
            listing = extracted_data.get('listing', {})
            price_suggestion = extracted_data.get('price_suggestion', {})
            
            # Format attributes for display
            attr_text = ""
            for key, value in attributes.items():
                if value and value != 'Unknown' and value != '_Not found_':
                    attr_text += f"• **{key}:** {value}\n"
                else:
                    attr_text += f"• **{key}:** _Not found_\n"

            confidence_emoji = "🟢" if confidence >= 0.7 else "🟡" if confidence >= 0.4 else "🔴"
            
            # Format price suggestion
            price_text = ""
            if price_suggestion and price_suggestion.get('max_price', 0) > 0:
                price_text = (f"� **Suggested Price:** ${price_suggestion['min_price']:.0f} - "
                            f"${price_suggestion['max_price']:.0f}\n"
                            f"_{price_suggestion.get('reasoning', '')}_\n\n")
            
            # Complete listing display
            message_text = (
                f"🎯 **Complete Listing Generated**\n\n"
                f"📝 **Title:** {listing.get('title', 'No title generated')}\n\n"
                f"📄 **Description:**\n{listing.get('description', 'No description provided')}\n\n"
                f"📊 **Product Details:**\n"
                f"🏷️ **Product:** {extracted_data['product_name']}\n"
                f"📁 **Category:** {extracted_data['category']}\n"
                f"📂 **Subcategory:** {extracted_data['subcategory']}\n"
                f"{confidence_emoji} **Confidence:** {confidence * 100:.0f}%\n\n"
                f"{price_text}"
                f"� **Attributes:**\n{attr_text}\n"
                f"Is this listing information correct?"
            )

            await message.edit(
                message_text,
                buttons=[
                    [
                        Button.inline("✅ Yes, Continue", "confirm_product"),
                        Button.inline("❌ No, Try Again", "reject_product")
                    ],
                    [Button.inline("🚫 Cancel Listing", "cancel_listing")]
                ],
                parse_mode="Markdown"
            )

        except Exception as e:
            logging.error(f"Error showing product confirmation: {e}")
            await message.edit("❌ Error displaying product information.")
    
    async def request_description(self, event, user_id: int):
        """Request user to input description manually"""
        try:
            session = self.session_manager.get_session_state(user_id)
            if not session:
                await event.answer("❌ Session not found.")
                return

            # Update session state to description input
            self.session_manager.update_session_state(user_id, ConversationState.DESCRIPTION_INPUT)

            # Get extracted data
            extracted_data = session['extracted_data']
            
            await event.edit(
                f"📝 **Write Your Description**\n\n"
                f"🏷️ Product: {extracted_data['product_name']}\n"
                f"📁 Category: {session['category']} → {session['subcategory']}\n\n"
                f"✍️ Please write a detailed description of your item:\n"
                f"• Condition (e.g., 8/10, excellent, good, etc.)\n"
                f"• How long you've used it\n"
                f"• Any important details buyers should know\n"
                f"• Mention if inspection is welcome\n\n"
                f"💬 **Example:** _\"Condition 8/10. Used for 2 years but well maintained. "
                f"All functions work perfectly. You can test everything in person. "
                f"Minor scratches on the back but screen is perfect. Bargaining welcome.\"_\n\n"
                f"Type your description below:",
                buttons=[[Button.inline("❌ Cancel", "cancel_listing")]],
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logging.error(f"Error requesting description: {e}")
            await event.answer("❌ Error requesting description.")
    
    async def request_price(self, event, user_id: int):
        """Request price input from user"""
        try:
            session = self.session_manager.get_session_state(user_id)
            if not session or not session.get('extracted_data'):
                await event.answer("❌ Session error. Please start over.")
                return

            # Update session state
            self.session_manager.update_session_state(user_id, ConversationState.PRICE_INPUT)

            # Get extracted data which now includes price suggestion
            extracted_data = session['extracted_data']
            price_suggestion = extracted_data.get('price_suggestion', {})
            
            suggestion_text = ""
            if price_suggestion and price_suggestion.get('max_price', 0) > 0:
                suggestion_text = (
                    f"\n💡 **Suggested Price Range:** "
                    f"${price_suggestion['min_price']:.0f} - ${price_suggestion['max_price']:.0f}\n"
                    f"_{price_suggestion.get('reasoning', '')}_\n"
                )

            await event.edit(
                f"💰 **Set Your Price**\n\n"
                f"🏷️ Product: {extracted_data['product_name']}\n"
                f"{suggestion_text}\n"
                f"Please enter your asking price (numbers only, e.g., 299.99):",
                buttons=[[Button.inline("❌ Cancel", "cancel_listing")]],
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logging.error(f"Error requesting price: {e}")
            await event.answer("❌ Error requesting price.")
    
    async def process_description_input(self, event, user_id: int, description_text: str):
        """Process manual description input from user"""
        try:
            # Validate description length
            description_text = description_text.strip()
            if len(description_text) < 10:
                await event.respond(
                    "❌ Description too short. Please provide at least 10 characters with useful details about your product."
                )
                return
            
            if len(description_text) > 500:
                await event.respond(
                    "❌ Description too long. Please keep it under 500 characters."
                )
                return
            
            # Store description in session
            self.session_manager.set_description(user_id, description_text)
            
            # Log action
            self.session_manager.log_user_action(
                user_id, 
                'description_entered', 
                {'description_length': len(description_text)}
            )
            
            # Confirm description received and ask for price
            await event.respond(
                f"✅ **Description saved:**\n\n{description_text}\n\n" +
                "💰 **Step 3: Set your price**\n" +
                "Enter the price for your product (e.g., 299.99 or 150)",
                parse_mode="Markdown"
            )
            
            # Move to price input state
            self.session_manager.update_session_state(user_id, ConversationState.PRICE_INPUT)
            
        except Exception as e:
            logging.error(f"Error processing description input: {e}")
            await event.respond("❌ An error occurred processing your description. Please try again.")
    
    async def process_price_input(self, event, user_id: int, price_text: str):
        """Process price input and complete the listing"""
        try:
            # Validate price format
            price_match = re.search(r'[\d.,]+', price_text.replace(',', '.'))
            if not price_match:
                await event.respond(
                    "❌ Invalid price format. Please enter a number (e.g., 299.99 or 150)."
                )
                return
            
            try:
                price = float(price_match.group().replace(',', '.'))
                if price <= 0 or price > 1000000:
                    await event.respond("❌ Price must be between 0.01 and 1,000,000.")
                    return
            except ValueError:
                await event.respond("❌ Invalid price. Please enter a valid number.")
                return
            
            # Get user info
            sender = await event.get_sender()
            username = sender.username or f"User_{sender.id}"
            
            # Get extracted data BEFORE completing listing (since complete_listing clears session)
            session = self.session_manager.get_session_state(user_id) or {}
            extracted_data = session.get('extracted_data', {})
            
            # Complete the listing
            product_id = self.session_manager.complete_listing(user_id, username, price)
            
            if product_id:
                # Add final price to extracted data for export
                extracted_data['final_price'] = price
                
                # Export to JSON file
                try:
                    json_filepath = self.exporter.export_listing(extracted_data, user_id, product_id)
                    logging.info(f"Listing exported to JSON: {json_filepath}")
                except Exception as export_error:
                    logging.error(f"Error exporting to JSON: {export_error}")
                    json_filepath = None
                
                # Get listing information and attributes
                listing = extracted_data.get('listing', {})
                attributes = extracted_data.get('attributes', {})
                
                # Format attributes for display
                attr_text = ""
                for key, value in attributes.items():
                    if value and value != 'Unknown' and value != '_Not found_':
                        attr_text += f"• **{key}:** {value}\n"
                
                # Show complete listing information
                message_text = (
                    f"🎉 **Listing Created Successfully!**\n\n"
                    f"🆔 **Listing ID:** #{product_id}\n\n"
                    f"📝 **Your Listing:**\n"
                    f"**Title:** {listing.get('title', extracted_data.get('product_name', 'Unknown'))}\n\n"
                    f"**Description:**\n{listing.get('description', 'No description available')}\n\n"
                    f"📊 **Details:**\n"
                    f"🏷️ **Product:** {extracted_data.get('product_name', 'Unknown')}\n"
                    f"📁 **Category:** {extracted_data.get('category', 'Unknown')}\n"
                    f"📂 **Subcategory:** {extracted_data.get('subcategory', 'Unknown')}\n"
                    f"💰 **Price:** ${price:.2f}\n\n"
                    f"🔧 **Product Attributes:**\n{attr_text if attr_text else 'No attributes extracted'}\n"
                    f"✅ **Saved to database!**\n"
                )
                
                if json_filepath:
                    message_text += f"📄 **Exported to JSON:** {json_filepath.split('/')[-1]}"
                
                await event.respond(message_text, parse_mode="Markdown")
            else:
                await event.respond("❌ Failed to save listing. Please try again.")
                
        except Exception as e:
            logging.error(f"Error processing price input: {e}")
            await event.respond("❌ Error processing price. Please try again.")
    
    async def cancel_listing(self, event, user_id: int, use_edit: bool = True):
        """Cancel current listing session"""
        try:
            if self.session_manager.cancel_listing(user_id):
                message_text = (
                    "🚫 **Listing Cancelled**\n\n"
                    "Your listing session has been cancelled. "
                    "You can start a new one anytime with /plaseaza_anunt."
                )
                
                if use_edit:
                    await event.edit(
                        message_text,
                        buttons=None,
                        parse_mode="Markdown"
                    )
                else:
                    await event.respond(
                        message_text,
                        parse_mode="Markdown"
                    )
            else:
                if use_edit:
                    await event.answer("❌ Error cancelling listing.")
                else:
                    await event.respond("❌ Error cancelling listing.")
                
        except Exception as e:
            logging.error(f"Error cancelling listing: {e}")
            if not use_edit:
                await event.respond("❌ Error cancelling listing.")
    
    async def handle_cancel_command(self, event):
        """Handle /cancel command"""
        try:
            sender = await event.get_sender()
            user_id = sender.id
            
            if self.session_manager.is_session_active(user_id):
                await self.cancel_listing(event, user_id, use_edit=False)
            else:
                await event.respond("ℹ️ No active listing session to cancel.")
                
        except Exception as e:
            logging.error(f"Error handling cancel command: {e}")
            await event.respond("❌ Error processing cancel command.")
    
    async def handle_status_command(self, event):
        """Handle /status command"""
        try:
            sender = await event.get_sender()
            user_id = sender.id
            
            summary = self.session_manager.get_session_summary(user_id)
            if summary:
                await event.respond(summary, parse_mode="Markdown")
            else:
                await event.respond("ℹ️ No active listing session. Use /plaseaza_anunt to start one!")
                
        except Exception as e:
            logging.error(f"Error handling status command: {e}")
            await event.respond("❌ Error getting status.")
    
    async def handle_my_listings_command(self, event):
        """Handle /my_listings command"""
        try:
            sender = await event.get_sender()
            user_id = sender.id
            
            products = self.storage.get_user_products(user_id, limit=5)
            
            if not products:
                await event.respond("📭 You haven't created any listings yet!")
                return
            
            listings_text = "📋 **Your Recent Listings:**\n\n"
            
            for product in products:
                status_emoji = "🟢" if product['status'] == 'active' else "🔴"
                listings_text += (
                    f"{status_emoji} **#{product['id']}** - {product['product_name']}\n"
                    f"💰 ${product['price']:.2f} | 📁 {product['category']}\n"
                    f"📅 {product['created_at'][:10]}\n\n"
                )
            
            await event.respond(listings_text, parse_mode="Markdown")
            
        except Exception as e:
            logging.error(f"Error handling my_listings command: {e}")
            await event.respond("❌ Error retrieving your listings.")