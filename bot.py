import os
import json
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
IMAGE_URL = os.environ.get("IMAGE_URL", "https://i.imgur.com/your_image_placeholder.jpg") 
TELEGRAM_CONTACT = "Logan207"
USERS_FILE = "users.json"

WELCOME_TEXT = (
    "Lost more than $2,000 on IQ Option, Binolla, ExpertOption, Exnova, or Quotex? "
    "I use my own capital to try to recover your trading losses. Contact me now.\n\n"
    "هل خسرت أكثر من 2,000 دولار على IQ Option أو Binolla أو ExpertOption أو Exnova أو Quotex؟ "
    "أستخدم مالي الخاص لمحاولة تعويض خسائرك في التداول. تواصل معي الآن.\n\n"
    "¿Perdiste más de $2,000 en IQ Option, Binolla, ExpertOption, Exnova o Quotex? "
    "Uso mi propio dinero para intentar recuperar tus pérdidas. Contáctame ahora.\n\n"
    f"Telegram: @{TELEGRAM_CONTACT}"
)

# --- Helper Functions for User Storage ---
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

async def send_welcome_message(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Sends the formatted message with button to a specific chat_id."""
    keyboard = [
        [InlineKeyboardButton(f"📩 Contact @{TELEGRAM_CONTACT}", url=f"https://t.me/{TELEGRAM_CONTACT}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=IMAGE_URL,
            caption=WELCOME_TEXT,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, saves the user, and sends the welcome message."""
    chat_id = update.message.chat_id
    
    # Save user
    users = load_users()
    if chat_id not in users:
        users.add(chat_id)
        save_users(users)
        logger.info(f"New user added: {chat_id}")

    # Send immediate welcome message
    await send_welcome_message(chat_id, context)

async def send_daily_broadcast(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job that runs every 24 hours to resend the message to all users."""
    users = load_users()
    logger.info(f"Starting daily broadcast to {len(users)} users...")
    
    for chat_id in users:
        await send_welcome_message(chat_id, context)
        await asyncio.sleep(0.1) # Small delay to avoid Telegram rate limits
        
    logger.info("Daily broadcast completed.")

def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Register the /start command
    application.add_handler(CommandHandler("start", start))

    # --- Set up the 24-Hour Job ---
    job_queue = application.job_queue
    if job_queue:
        # Runs every 86400 seconds (24 hours). 
        # 'first' is set to 10 seconds so you can test it right after deployment.
        # Change 'first' to 86400 when you are ready for production.
        job_queue.run_repeating(send_daily_broadcast, interval=86400, first=10)
        logger.info("Daily broadcast job scheduled.")

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
