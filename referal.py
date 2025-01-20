import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import aiomysql

# Load environment variables from .env file
load_dotenv()

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_NAME"),
}
SUDO_USERS = [
    int(uid.strip())
    for uid in os.getenv("SUDO_USERS", "7943250659").split(",")
    if uid.strip().isdigit()
]

# Initialize database
async def init_db():
    try:
        pool = await aiomysql.create_pool(**DB_CONFIG, autocommit=True)
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS botusers (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        refcount INT DEFAULT 0,
                        balance INT DEFAULT 0,
                        name VARCHAR(255),
                        invitedby BIGINT
                    )
                """)
        pool.close()
        await pool.wait_closed()
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing the database: {e}")

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username
    name = user.first_name or "User"
    referrer_id = int(context.args[0]) if context.args else None

    try:
        pool = await aiomysql.create_pool(**DB_CONFIG)
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if user already exists
                await cursor.execute("SELECT user_id FROM botusers WHERE user_id = %s", (user_id,))
                result = await cursor.fetchone()

                if not result:
                    # Insert new user
                    await cursor.execute(
                        """
                        INSERT INTO botusers (user_id, username, name, invitedby)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (user_id, username, name, referrer_id),
                    )
                    if referrer_id:
                        # Update refcount and balance for the referrer
                        await cursor.execute(
                            """
                            UPDATE botusers
                            SET refcount = refcount + 1, balance = balance + 38
                            WHERE user_id = %s
                            """,
                            (referrer_id,),
                        )
        pool.close()
        await pool.wait_closed()

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("1️⃣ КАНАЛ", url="https://t.me/+wtei_zPm4803N2Iy")],
                [InlineKeyboardButton("2️⃣ КАНАЛ", url="https://t.me/+f_i1-UN7HdplNGEy")],
                [InlineKeyboardButton("Тексеру", callback_data="check_subscription")],
            ]
        )
        await update.message.reply_text(
            f"Сәлем, {name}! Сіз демеушілерге жазылмағансыз. Жазылуыңызды өтінемін.",
            reply_markup=keyboard,
        )
    except Exception as e:
        print(f"Error in /start handler: {e}")
        await update.message.reply_text("Қате пайда болды. Қайтадан көріңіз.")

# Check subscription callback handler
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        ch1 = await context.bot.get_chat_member(chat_id="-1002494327985", user_id=user_id)
        ch2 = await context.bot.get_chat_member(chat_id="-1002184512508", user_id=user_id)

        is_subscribed = (
            ch1.status in ["member", "administrator", "creator"]
            and ch2.status in ["member", "administrator", "creator"]
        )

        if is_subscribed:
            pool = await aiomysql.create_pool(**DB_CONFIG, autocommit=True)
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE botusers SET balance = balance + 10 WHERE user_id = %s", (user_id,)
                    )
            pool.close()
            await pool.wait_closed()

            main_menu = ReplyKeyboardMarkup(
                [["Жеке Кабинет 🙋‍♂️", "Ақша Табу 💵"], ["Ақпарат 📚"]],
                resize_keyboard=True,
            )
            await query.message.reply_text(
                "<b>Басты мәзір ⤵️</b>", parse_mode="HTML", reply_markup=main_menu
            )
        else:
            await query.message.reply_text("Өтінемін, барлық демеушілерге жазылыңыз.")
    except Exception as e:
        print(f"Error in check_subscription: {e}")
        await query.message.reply_text("Қате пайда болды. Қайтадан көріңіз.")
    finally:
        await query.answer()

# Personal cabinet handler
async def personal_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        pool = await aiomysql.create_pool(**DB_CONFIG)
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT balance, refcount FROM botusers WHERE user_id = %s", (user_id,)
                )
                user_info = await cursor.fetchone()
                balance = user_info["balance"] if user_info else 0
                refcount = user_info["refcount"] if user_info else 0

        pool.close()
        await pool.wait_closed()

        await update.message.reply_text(
            f"Жеке кабинет 🔰\n\n==============================\nБарлық рефералдар саны 📈: {refcount}\nТабысыңыз: {balance} тг"
        )
    except Exception as e:
        print(f"Error in personal cabinet handler: {e}")
        await update.message.reply_text("Қате пайда болды. Қайтадан көріңіз.")

# Earn money handler
async def earn_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    referral_link = f"t.me/adal_tenge_bot?start={update.effective_user.id}"
    await update.message.reply_text(
        f"Ақша табу үшін сілтемеңізді бөлісіңіз 👉\n"
        f"Сізге +38 тг шақырған адамыңыз демеушілерге тіркелгенде берілетін болады💚: {referral_link}"
    )

# Information handler
async def information(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бұл бот каналдарға жазылу арқылы , және өз достарыңызбен бөлісу арқылы ақша табуға көмектесетін Қазақстандық бот! \n\n"
        "Әрбір тіркелген адам үшін +38 тг берілетін болады😍"
    )

# Error handler to catch all unexpected errors
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"An unexpected error occurred: {context.error}")
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Қате пайда болды. Қайтадан көріңіз.")

# Main function to start the bot
async def main():
    await init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    application.add_handler(
        MessageHandler(
            filters.Regex("Жеке Кабинет 🙋‍♂️"), personal_cabinet
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("Ақша Табу 💵"), earn_money
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("Ақпарат 📚"), information
        )
    )

    # Register error handler
    application.add_error_handler(error_handler)

    print("Bot is running...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())