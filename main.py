import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

CHANNEL_MAPPING = {
    "menfess": {"chat_id": -1003033445498, "thread_id": 393},
    "moan_cwo": {"chat_id": -1003014574672, "thread_id": 392},
    "moan_cwe": {"chat_id": -1002931160816, "thread_id": 391},
    "pap_cwo": {"chat_id": -1003057432597, "thread_id": 812},
    "pap_cwe": {"chat_id": -1002863900535, "thread_id": 816},
    "fwb": {"chat_id": -1002897403070, "thread_id": 806},
    "nakal_main": {"chat_id": -1003098333444, "thread_id": None},
    "bdsm": {"chat_id": -1002987029269, "thread_id": 343},
    "looking_partner": {"chat_id": -1002897403070, "thread_id": 806},  # contoh
}

HASHTAGS = {
    "menfess": "#menfess",
    "curhat": "#curhat",
    "cerita18+": "#cerita18+",
    "keluhkesah": "#keluhkesah",
}

EMOJI_LIST = ["🔥", "💦", "😍"]

user_state = {}      # {user_id: {"topic":..., "hashtag":..., "gender":..., "last_message_id":..., "show_id":...}}
reaction_data = {}   # {message_id: {emoji: set(user_ids)}}

# ======= START & PILIH TOPIK =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(topic, callback_data=f"topic_{topic}")] for topic in CHANNEL_MAPPING.keys()]
    await update.message.reply_text("📌 Pilih topik:", reply_markup=InlineKeyboardMarkup(keyboard))

async def topic_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic = query.data.replace("topic_", "")
    user_id = query.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["topic"] = topic

    # Menfess dengan hashtag
    if topic == "menfess":
        keyboard = [[InlineKeyboardButton(f"{tag} {desc}", callback_data=f"hashtag_{tag}")] for tag, desc in {
            "menfess": "fess umum",
            "curhat": "isi hati / 18+",
            "cerita18+": "pengalaman 18+",
            "keluhkesah": "tempat mengeluh"
        }.items()]
        await query.message.reply_text("Pilih hashtag untuk Menfess-mu:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif topic == "looking_partner":
        keyboard = [[InlineKeyboardButton("Tampilkan ID", callback_data="show_id_yes")],
                    [InlineKeyboardButton("Sembunyikan ID", callback_data="show_id_no")]]
        await query.message.reply_text("Apakah kamu ingin menampilkan ID untuk calon partner?", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.message.reply_text(f"Topik '{topic}' dipilih. Silakan kirim pesan / media.")

async def hashtag_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tag = query.data.replace("hashtag_", "")
    user_id = query.from_user.id
    user_state[user_id]["hashtag"] = tag
    await query.message.reply_text(f"Hashtag {HASHTAGS.get(tag,'#menfess')} dipilih. Silakan kirim pesan Menfess-mu.")

async def show_id_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data.replace("show_id_", "")
    user_state[user_id]["show_id"] = choice == "yes"
    await query.message.reply_text(f"ID user akan {'ditampilkan' if choice=='yes' else 'disembunyikan'}. Silakan kirim pesan.")

# ======= HANDLE PESAN =======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_state or "topic" not in user_state[user_id]:
        await update.message.reply_text("Ketik /start untuk memilih topik.")
        return

    topic = user_state[user_id]["topic"]
    mapping = CHANNEL_MAPPING.get(topic)
    if not mapping:
        await update.message.reply_text("Topik tidak ditemukan.")
        return

    chat_id = mapping["chat_id"]
    thread_id = mapping["thread_id"]
    text = update.message.text or ""

    # Menambahkan ID jika diaktifkan
    if user_state[user_id].get("show_id", False):
        text += f"\nID: {user_id}"

    sent_msg = None
    if update.message.photo:
        sent_msg = await context.bot.send_photo(chat_id=chat_id, photo=update.message.photo[-1].file_id,
                                                caption=text, message_thread_id=thread_id)
    elif update.message.video:
        sent_msg = await context.bot.send_video(chat_id=chat_id, video=update.message.video.file_id,
                                                caption=text, message_thread_id=thread_id)
    else:
        sent_msg = await context.bot.send_message(chat_id=chat_id, text=text, message_thread_id=thread_id)

    # Notifikasi admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"[{topic}] Pesan baru dari user {user_id}.")
        except:
            continue

    await update.message.reply_text("✅ Pesan berhasil dikirim!")

    # Tambah reaction keyboard
    if sent_msg:
        await add_reaction_keyboard(sent_msg, context)
        user_state[user_id]["last_message_id"] = sent_msg.message_id

# ======= REACTION EMOJI =======
async def add_reaction_keyboard(message, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"{emoji} 0", callback_data=f"react_{emoji}_{message.message_id}") for emoji in EMOJI_LIST]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.edit_message_reply_markup(chat_id=message.chat_id, message_id=message.message_id, reply_markup=reply_markup)
    except:
        pass
    reaction_data[message.message_id] = {emoji: set() for emoji in EMOJI_LIST}

async def reaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    if not data.startswith("react_"):
        return

    _, emoji, msg_id_str = data.split("_")
    msg_id = int(msg_id_str)
    if msg_id not in reaction_data:
        reaction_data[msg_id] = {e: set() for e in EMOJI_LIST}

    # Toggle
    if user_id in reaction_data[msg_id][emoji]:
        reaction_data[msg_id][emoji].remove(user_id)
    else:
        reaction_data[msg_id][emoji].add(user_id)

    # Update keyboard
    keyboard = [[InlineKeyboardButton(f"{e} {len(reaction_data[msg_id][e])}", callback_data=f"react_{e}_{msg_id}") for e in EMOJI_LIST]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id, message_id=msg_id, reply_markup=reply_markup)
    except:
        pass

# ======= MAIN =======
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(topic_choice, pattern=r"^topic_"))
    app.add_handler(CallbackQueryHandler(hashtag_choice, pattern=r"^hashtag_"))
    app.add_handler(CallbackQueryHandler(show_id_choice, pattern=r"^show_id_"))
    app.add_handler(CallbackQueryHandler(reaction_handler, pattern=r"^react_"))
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, handle_message))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
