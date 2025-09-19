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
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN belum diset! Cek environment variable di Render.")

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS belum diset! Cek environment variable di Render.")

# Channel mapping
CHANNEL_MAPPING = {
    "menfess": {"chat_id": -1003033445498, "thread_id": 393},
    "moan_cwo": {"chat_id": -1003014574672, "thread_id": 392},
    "moan_cwe": {"chat_id": -1002931160816, "thread_id": 391},
    "pap_cwo": {"chat_id": -1003057432597, "thread_id": 812},
    "pap_cwe": {"chat_id": -1002863900535, "thread_id": 816},
    "fwb": {"chat_id": -1002897403070, "thread_id": 806},
    "nakal_main": {"chat_id": -1003098333444, "thread_id": None},
    "bdsm": {"chat_id": -1002987029269, "thread_id": 343},
}

HASHTAGS = {
    "menfess": "#menfess",
    "curhat": "#curhat",
    "cerita18+": "#cerita18+",
    "keluhkesah": "#keluhkesah",
}

EMOJI_LIST = ["🔥", "💦", "😍"]

# State
user_state = {}      # {user_id: {"topic":..., "hashtag":..., "gender":..., "show_id":..., "last_message_id":...}}
reaction_data = {}   # {message_id: {emoji: set(user_ids)}}

# ================== PILIH GENDER ==================
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    keyboard = [
        [InlineKeyboardButton("Cewek 👩‍🦰", callback_data="gender_cwe")],
        [InlineKeyboardButton("Cowok 👦", callback_data="gender_cwo")],
    ]
    await update.message.reply_text(
        "Pilih gender kamu untuk pesan anonim:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def gender_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    gender = query.data.replace("gender_", "")
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["gender"] = gender
    await query.message.reply_text(
        "✅ Gender tersimpan. Sekarang ketik /start untuk pilih topik."
    )

# ================== START & PILIH TOPIK ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    user_id = update.message.from_user.id
    if user_id not in user_state or "gender" not in user_state[user_id]:
        await ask_gender(update, context)
        return

    keyboard = [[InlineKeyboardButton(name, callback_data=f"topic_{name}")] for name in CHANNEL_MAPPING.keys()]
    await update.message.reply_text(
        "📌 Pilih topik yang ingin kamu kirim:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def topic_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    topic = query.data.replace("topic_", "")
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["topic"] = topic

    if topic == "menfess":
        keyboard = [
            [InlineKeyboardButton(f"{tag} {desc}", callback_data=f"hashtag_{tag}")]
            for tag, desc in {
                "menfess": "fess umum",
                "curhat": "isi hati / 18+",
                "cerita18+": "pengalaman 18+",
                "keluhkesah": "tempat mengeluh",
            }.items()
        ]
        await query.message.reply_text(
            "Pilih hashtag untuk pesan Menfess-mu:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif topic in ["fwb", "nakal_main", "bdsm"]:
        keyboard = [
            [InlineKeyboardButton("Tampilkan ID ke calon partner", callback_data="showid_yes")],
            [InlineKeyboardButton("Sembunyikan ID", callback_data="showid_no")],
        ]
        await query.message.reply_text(
            "Apakah kamu ingin menampilkan ID untuk Looking Partner / FWB / BDSM?", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.message.reply_text(
            f"Topik '{topic}' dipilih. Sekarang kirim pesan / media sesuai topik."
        )

async def hashtag_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tag = query.data.replace("hashtag_", "")
    if user_id in user_state:
        user_state[user_id]["hashtag"] = tag
    await query.message.reply_text(
        f"Hashtag {HASHTAGS.get(tag, '')} dipilih. Silakan kirim pesan Menfess-mu sekarang."
    )

async def showid_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data.replace("showid_", "")
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["show_id"] = (choice == "yes")
    await query.message.reply_text("✅ Pilihan tersimpan. Silakan kirim pesan / media sekarang.")

# ================== HANDLE PESAN ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    user_id = update.message.from_user.id
    if user_id not in user_state or "topic" not in user_state[user_id] or "gender" not in user_state[user_id]:
        await update.message.reply_text("Ketik /start untuk mulai dan pilih gender.")
        return

    topic = user_state[user_id]["topic"]
    channel_info = CHANNEL_MAPPING.get(topic)
    if not channel_info:
        await update.message.reply_text("Topik tidak dikenal.")
        return

    thread_id = channel_info["thread_id"]
    chat_id = channel_info["chat_id"]
    gender = user_state[user_id]["gender"]

    # Format gender
    gender_text = f"🕵️ Pesan anonim dari: {'👩‍🦰 Cewek' if gender=='cwe' else '👦 Cowok'}\n\n"

    # Append ID jika user ingin tampilkan
    if user_state[user_id].get("show_id"):
        gender_text += f"ID Telegram: {user_id}\n\n"

    sent_msg = None

    # ======= MENFESS =======
    if topic == "menfess":
        text = update.message.text or ""
        if not text:
            await update.message.reply_text("Kirim pesan teks untuk Menfess.")
            return
        hashtag = HASHTAGS.get(user_state[user_id].get("hashtag"), "#menfess")
        full_text = f"{gender_text}{text}\n\n{hashtag}"
        sent_msg = await context.bot.send_message(chat_id=chat_id, text=full_text, message_thread_id=thread_id)

    # ======= FOTO / VIDEO =======
    elif topic in ["pap_cwo", "pap_cwe", "nakal_main", "bdsm", "fwb"]:
        if update.message.photo:
            sent_msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=update.message.photo[-1].file_id,
                caption=gender_text + (update.message.caption or ""),
                message_thread_id=thread_id
            )
        elif update.message.video:
            sent_msg = await context.bot.send_video(
                chat_id=chat_id,
                video=update.message.video.file_id,
                caption=gender_text + (update.message.caption or ""),
                message_thread_id=thread_id
            )
        elif update.message.audio or update.message.voice:
            file_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
            if update.message.voice:
                sent_msg = await context.bot.send_voice(chat_id=chat_id, voice=file_id, caption=gender_text, message_thread_id=thread_id)
            else:
                sent_msg = await context.bot.send_audio(chat_id=chat_id, audio=file_id, caption=gender_text, message_thread_id=thread_id)
        else:
            await update.message.reply_text("Topik ini hanya menerima media (foto, video, voice/audio).")
            return

    # ======= NOTIF ADMIN =======
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"[{topic}] Pesan baru diterima dari user {user_id}.")
        except:
            continue

    await update.message.reply_text(f"Pesan berhasil dikirim ke topik '{topic}'.")

    # ======= REACTION EMOJI =======
    if sent_msg:
        user_state[user_id]["last_message_id"] = sent_msg.message_id
        await add_reaction_keyboard(sent_msg, context)

# ================== REACTION ==================
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

    _, emoji, msg_id = data.split("_")
    msg_id = int(msg_id)

    if msg_id not in reaction_data:
        reaction_data[msg_id] = {e: set() for e in EMOJI_LIST}

    user_set = reaction_data[msg_id].setdefault(emoji, set())
    if user_id in user_set:
        user_set.remove(user_id)
    else:
        user_set.add(user_id)

    # Update keyboard counts
    keyboard = [[InlineKeyboardButton(f"{e} {len(reaction_data[msg_id].get(e,set()))}", callback_data=f"react_{e}_{msg_id}") for e in EMOJI_LIST]]
    try:
        await context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=msg_id, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        pass

# ================== RUN BOT ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gender", ask_gender))
    app.add_handler(CallbackQueryHandler(gender_choice, pattern="^gender_"))
    app.add_handler(CallbackQueryHandler(topic_choice, pattern="^topic_"))
    app.add_handler(CallbackQueryHandler(hashtag_choice, pattern="^hashtag_"))
    app.add_handler(CallbackQueryHandler(showid_choice, pattern="^showid_"))
    app.add_handler(CallbackQueryHandler(reaction_handler, pattern="^react_"))
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, handle_message))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
