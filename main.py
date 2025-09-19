import os
import random
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

# Channel & GC
GROUP_ID = int(os.getenv("GROUP_ID"))  # Menfess biasa
LOOKING_PARTNER_CHANNEL = int(os.getenv("LOOKING_PARTNER_CHANNEL"))
DISCUSSION_GC_ID = int(os.getenv("DISCUSSION_GC_ID"))

# Channel mapping topik
CHANNEL_MAPPING = {
    "Menfess": GROUP_ID,
    "lookingpartner": LOOKING_PARTNER_CHANNEL,
    "BDSM Community": -1002987029269,
    "Pap Cwo": -1003057432597,
    "Pap Cwe": -1002863900535,
    "Fwb / Dating": -1002897403070,
}

# Thread mapping topik
TOPICS = {
    "Moan Cwo": 392,
    "Moan Cwe": 391,
    "Menfess": 393,
    "Pap Cwo": 812,
    "Pap Cwe": 816,
    "Fwb / Dating": 806,
    "BDSM Community": 343,
}

HASHTAGS = {
    "menfess": "#menfess",
    "curhat": "#curhat",
    "cerita18+": "#cerita18+",
    "keluhkesah": "#keluhkesah",
    "lookingpartner": "#lookingpartner",
}

EMOJI_LIST = ["🔥", "💦", "😍"]

user_state = {}      # {user_id: {topic, hashtag, gender, lp_show, last_message_id}}
reaction_data = {}   # {message_id: {emoji: set(user_ids)}}

# ====================== GENDER ======================
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Cewek 👩‍🦰", callback_data="gender_cwe")],
        [InlineKeyboardButton("Cowok 👦", callback_data="gender_cwo")],
    ]
    await update.message.reply_text("Pilih gender kamu untuk pesan anonim:", reply_markup=InlineKeyboardMarkup(keyboard))


async def gender_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    gender = query.data.replace("gender_", "")
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["gender"] = gender
    await query.message.reply_text("✅ Gender tersimpan. Ketik /start untuk pilih topik.")


# ====================== START & TOPIC ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    user_id = update.message.from_user.id
    if user_id not in user_state or "gender" not in user_state[user_id]:
        await ask_gender(update, context)
        return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"topic_{name}")] for name in TOPICS.keys()]
    await update.message.reply_text("📌 Pilih topik yang ingin kamu kirim:", reply_markup=InlineKeyboardMarkup(keyboard))


async def topic_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    topic = query.data.replace("topic_", "")
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["topic"] = topic

    if topic == "Menfess":
        keyboard = [
            [InlineKeyboardButton(f"{tag} {desc}", callback_data=f"hashtag_{tag}")]
            for tag, desc in {
                "menfess": "fess umum",
                "curhat": "isi hati / 18+",
                "cerita18+": "pengalaman 18+",
                "keluhkesah": "tempat mengeluh",
                "lookingpartner": "cari partner",
            }.items()
        ]
        await query.message.reply_text("Pilih hashtag untuk pesan Menfess-mu:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.message.reply_text(f"Topik '{topic}' dipilih. Silakan kirim pesan / media sesuai topik.")


# ====================== HASHTAG ======================
async def hashtag_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tag = query.data.replace("hashtag_", "")
    if user_id in user_state:
        user_state[user_id]["hashtag"] = tag
    if tag == "lookingpartner":
        await ask_lp_id_choice(query, context)
    else:
        await query.message.reply_text(f"Hashtag {HASHTAGS.get(tag, '')} dipilih. Silakan kirim pesan Menfess-mu sekarang.")


# ====================== LP-ID ======================
async def ask_lp_id_choice(query, context):
    keyboard = [
        [InlineKeyboardButton("Tampilkan ID", callback_data="lp_show")],
        [InlineKeyboardButton("Sembunyikan ID", callback_data="lp_hide")],
    ]
    await query.message.reply_text("Apakah kamu ingin menampilkan ID Looking Partner?", reply_markup=InlineKeyboardMarkup(keyboard))


async def lp_id_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["lp_show"] = query.data == "lp_show"
    await query.message.reply_text("✅ Opsi ID tersimpan. Silakan kirim pesan Menfess-mu sekarang.")


def generate_lp_id():
    return f"LP-{random.randint(1000, 9999)}"


# ====================== HANDLE MESSAGE ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    user_id = update.message.from_user.id
    if user_id not in user_state or "topic" not in user_state[user_id] or "gender" not in user_state[user_id]:
        await update.message.reply_text("Ketik /start untuk mulai dan pilih gender.")
        return

    topic = user_state[user_id]["topic"]
    gender = user_state[user_id]["gender"]
    gender_text = "🕵️ Pesan anonim\n\n"
    if gender == "cwe":
        gender_text = "🕵️ Pesan anonim dari: 👩‍🦰\nCewek\n\n"
    elif gender == "cwo":
        gender_text = "🕵️ Pesan anonim dari: 👦\nCowok\n\n"

    text = update.message.text or ""
    sent_msg = None

    # ======= Tentukan channel =======
    if topic == "Menfess" and user_state[user_id].get("hashtag") == "lookingpartner":
        channel_id = CHANNEL_MAPPING.get("lookingpartner")
    else:
        channel_id = CHANNEL_MAPPING.get(topic, GROUP_ID)

    thread_id = TOPICS.get(topic)

    # ======= Menfess / Looking Partner =======
    if topic == "Menfess":
        hashtag = HASHTAGS.get(user_state[user_id].get("hashtag"), "#menfess")
        lp_id_text = ""
        if user_state[user_id].get("lp_show") and user_state[user_id].get("hashtag") == "lookingpartner":
            lp_id = generate_lp_id()
            user_state[user_id]["lp_id"] = lp_id
            lp_id_text = f" | ID: {lp_id}"

        full_text = f"{gender_text.strip()}{lp_id_text}\n\n{text}\n\n{hashtag}"

        sent_msg = await context.bot.send_message(chat_id=channel_id, text=full_text, message_thread_id=thread_id)

        # Forward ke GC diskusi
        await context.bot.send_message(chat_id=DISCUSSION_GC_ID, text=full_text)

    # ======= Foto / Video =======
    elif topic in ["Pap Cwo", "Pap Cwe", "BDSM Community"]:
        if update.message.photo:
            sent_msg = await context.bot.send_photo(chat_id=channel_id, photo=update.message.photo[-1].file_id,
                                                   caption=gender_text + (update.message.caption or ""),
                                                   message_thread_id=thread_id)
        elif update.message.video:
            sent_msg = await context.bot.send_video(chat_id=channel_id, video=update.message.video.file_id,
                                                    caption=gender_text + (update.message.caption or ""),
                                                    message_thread_id=thread_id)
        else:
            await update.message.reply_text("Topik ini hanya menerima foto atau video.")
            return

    # ======= Voice / Audio =======
    elif topic in ["Moan Cwo", "Moan Cwe"]:
        if update.message.voice:
            sent_msg = await context.bot.send_voice(chat_id=channel_id, voice=update.message.voice.file_id,
                                                    caption=gender_text + (update.message.caption or ""),
                                                    message_thread_id=thread_id)
        elif update.message.audio:
            sent_msg = await context.bot.send_audio(chat_id=channel_id, audio=update.message.audio.file_id,
                                                    caption=gender_text + (update.message.caption or ""),
                                                    message_thread_id=thread_id)
        else:
            await update.message.reply_text("Topik ini hanya menerima voice/audio.")
            return
    else:
        await update.message.reply_text("Topik tidak dikenal.")
        return

    # ======= Notif Admin =======
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"[{topic}] Pesan baru dari user {user_id}.")
        except:
            pass

    await update.message.reply_text(f"Pesan berhasil dikirim ke topik '{topic}'.")

    # ======= Reaction Emoji =======
    if sent_msg:
        user_state[user_id]["last_message_id"] = sent_msg.message_id
        await add_reaction_keyboard(sent_msg, context)


# ====================== REACTION ======================
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
    if user_id in reaction_data[msg_id][emoji]:
        reaction_data[msg_id][emoji].remove(user_id)
    else:
        reaction_data[msg_id][emoji].add(user_id)

    keyboard = [[InlineKeyboardButton(f"{e} {len(reaction_data[msg_id][e])}", callback_data=f"react_{e}_{msg_id}") for e in EMOJI_LIST]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.edit_message_reply_markup(chat_id=CHANNEL_MAPPING.get("Menfess", GROUP_ID), message_id=msg_id, reply_markup=reply_markup)
    except:
        pass


# ====================== MAIN ======================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(gender_choice, pattern="^gender_"))
    app.add_handler(CallbackQueryHandler(topic_choice, pattern="^topic_"))
    app.add_handler(CallbackQueryHandler(hashtag_choice, pattern="^hashtag_"))
    app.add_handler(CallbackQueryHandler(lp_id_choice, pattern="^lp_"))
    app.add_handler(CallbackQueryHandler(reaction_handler, pattern="^react_"))
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, handle_message))
    print("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
