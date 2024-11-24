import os
from pytube import YouTube
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters
import requests

BOT_TOKEN = "7871437492:AAGlhAIOYhBsAW7PFJXpr3w5bEd7XwBrCZw"
CHANNEL_1_ID = "@hikvik"
CHANNEL_2_ID = "@hikvik"


USER_DATA_FILE = 'user_data.txt'


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


ADMIN_ID = [6393985738]


def save_user_data(user_id, username):
    with open(USER_DATA_FILE, 'a') as file:
        file.write(f"{user_id},@{username}\n")


async def is_subscribed(user_id: int, channel_id: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={channel_id}&user_id={user_id}"
    response = requests.get(url).json()
    return response.get("ok", False) and response.get("result", {}).get("status") in ("member", "administrator", "creator")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    save_user_data(user.id, user.username)

    link_buttons = [
        [InlineKeyboardButton("Channel 1", url=f"https://t.me/{CHANNEL_1_ID[1:]}")],
        [InlineKeyboardButton("Channel 2", url=f"https://t.me/{CHANNEL_2_ID[1:]}")],
        [InlineKeyboardButton("Verify Subscription", callback_data="verify_subscription")],
    ]
    keyboard = InlineKeyboardMarkup(link_buttons)

    await update.message.reply_text(
        f"Welcome, {user.first_name}! Please subscribe to the channels and verify your subscription.",
        reply_markup=keyboard
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id in ADMIN_ID:
        with open(USER_DATA_FILE, 'r') as file:
            data = file.read()
        await update.message.reply_text(f"User Data:\n{data}")
    else:
        await update.message.reply_text("Access denied!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = update.message.text
    user = update.effective_user

    if "youtube.com" in link or "youtu.be" in link:
        subscribed_channel_1 = await is_subscribed(user.id, CHANNEL_1_ID)
        subscribed_channel_2 = await is_subscribed(user.id, CHANNEL_2_ID)

        if subscribed_channel_1 and subscribed_channel_2:
            await download_youtube_video(context, update, link)
        else:
            await start(update, context)
    else:
        await update.message.reply_text("Please send a valid YouTube link!")


async def download_youtube_video(context: ContextTypes.DEFAULT_TYPE, update: Update, link: str) -> None:
    try:
        yt = YouTube(link)
        video_stream = yt.streams.get_highest_resolution()
        file_path = video_stream.download(output_path=DOWNLOAD_DIR)

        with open(file_path, "rb") as video:
            await update.message.reply_text("Sending downloaded YouTube video...")
            await context.bot.send_document(chat_id=update.message.chat_id, document=video)

        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"Failed to download YouTube video: {str(e)}")


async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if query.data == "verify_subscription":
        subscribed_channel_1 = await is_subscribed(user.id, CHANNEL_1_ID)
        subscribed_channel_2 = await is_subscribed(user.id, CHANNEL_2_ID)

        if subscribed_channel_1 and subscribed_channel_2:
            await query.edit_message_text("You are successfully subscribed to both channels! You can now send links.")
        else:
            await query.edit_message_text(
                "You need to subscribe to both channels to use the bot.\n"
                "Please subscribe and click 'Verify Subscription' again to continue."
            )


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(inline_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


app.run_polling()
