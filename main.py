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

# ================== ENV VAR ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

# Channel / group utama
CHANNEL_MAPPING = {
    "Menfess": int(os.getenv("GROUP_ID", "-1003033445498")),
    "Looking Partner": int(os.getenv("LOOKING_PARTNER_CHANNEL", "-1003014574672")),
    "Discussion GC": int(os.getenv("DISCUSSION_GC_ID", "-1002931160816")),
    "Moan Cwo": -1003014574672,
    "Moan Cwe": -1002931160816,
    "Pap Cwo": -1003057432597,
    "Pap Cwe": -1002863900535,
    "BDSM": -1002987029269,
}

THREADS = {
    "Moan Cwo": 392,
    "Moan Cwe": 391,
    "Menfess": 393,
    "Pap Cwo": 812,
    "Pap Cwe": 816,
    "FWB": 806,
    "BDSM": 343,
}

HASHTAGS = {
    "menfess": "#menfess",
    "curhat": "#curhat",
    "cerita18+": "#cerita18+",
    "keluhkesah": "#keluhkesah",
    "lookingpartner": "#lookingpartner",
}

EMOJI_LIST = ["🔥", "💦", "😍"]

# ================== STATE ==================
user_state = {}      # {user_id: {"topic":..., "hashtag":..., "gender":..., "show_id":..., "last_message_id":...}}
reaction_data = {}   # {message_id: {emoji: set(user_ids)}}

# ================== GENDER ==================
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

# ================== START & TOPIC ==================
TOPICS = ["Menfess", "Looking Partner", "Pap Cwo", "Pap Cwe", "Moan Cwo", "Moan Cwe", "BDSM", "FWB"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    user_id = update.message.from_user.id
    if user_id not in user_state or "gender" not in user_state[user_id]:
        await ask_gender(update, context)
        return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"topic_{name}")] for name in TOPICS]
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

    if topic in ["Menfess", "Looking Partner"]:
        keyboard = [
            [InlineKeyboardButton(f"{tag}", callback_data=f"hashtag_{tag}")]
            for tag in HASHTAGS.keys()
        ]
        await query.message.reply_text(
            f"Pilih hashtag untuk topik '{topic}':", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif topic == "Looking Partner":
        keyboard = [
            [
                InlineKeyboardButton("Tampilkan ID", callback_data="lp_showid"),
                InlineKeyboardButton("Sembunyikan ID", callback_data="lp_hideid")
            ]
        ]
        await query.message.reply_text(
            "Apakah kamu ingin menampilkan ID untuk calon partner?", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.message.reply_text(
            f"Topik '{topic}' dipilih. Silakan kirim pesan sesuai topik."
        )

# ================== HASHTAG ==================
async def hashtag_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tag = query.data.replace("hashtag_", "")
    user_id = query.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["hashtag"] = tag
    await query.message.reply_text(f"Hashtag {HASHTAGS.get(tag,'#menfess')} dipilih. Silakan kirim pesan sekarang.")

# ================== SHOW ID ==================
async def lp_id_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {}
    if query.data == "lp_showid":
        user_state[user_id]["show_id"] = True
        await query.message.reply_text("✅ ID akan ditampilkan di pesan Looking Partner.")
    else:
        user_state[user_id]["show_id"] = False
        await query.message.reply_text("✅ ID tidak akan ditampilkan.")

# ================== HANDLE MESSAGE ==================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    user_id = update.message.from_user.id
    if user_id not in user_state or "topic" not in user_state[user_id] or "gender" not in user_state[user_id]:
        await update.message.reply_text("Ketik /start untuk mulai dan pilih gender.")
        return
    topic = user_state[user_id]["topic"]
    thread_id = THREADS.get(topic)
    gender = user_state[user_id]["gender"]
    show_id = user_state[user_id].get("show_id", False)

    # Format gender + ID
    gender_text = f"🕵️ Pesan anonim dari: {'👩‍🦰' if gender=='cwe' else '👦'}\n{ 'Cewek' if gender=='cwe' else 'Cowok' }"
    if topic == "Looking Partner" and show_id:
        gender_text += f" | ID: LP-{user_id%10000}"

    # Tentukan channel
    if topic in ["Menfess"]:
        channel_id = CHANNEL_MAPPING["Menfess"]
        text = update.message.text or ""
        full_text = f"{gender_text}\n\n{text}\n\n{HASHTAGS.get(user_state[user_id].get('hashtag'),'#menfess')}"
        sent_msg = await context.bot.send_message(chat_id=channel_id, text=full_text, message_thread_id=thread_id)

    elif topic == "Looking Partner":
        channel_id = CHANNEL_MAPPING["Looking Partner"]
        text = update.message.text or ""
        full_text = f"{gender_text}\n\n{text}\n\n{HASHTAGS.get(user_state[user_id].get('hashtag'),'#lookingpartner')}"
        sent_msg = await context.bot.send_message(chat_id=channel_id, text=full_text, message_thread_id=thread_id)

    elif topic in ["Pap Cwo","Pap Cwe","BDSM"]:
        channel_id = CHANNEL_MAPPING.get(topic, CHANNEL_MAPPING["BDSM"])
        if update.message.photo:
            sent_msg = await context.bot.send_photo(
                chat_id=channel_id,
                photo=update.message.photo[-1].file_id,
                caption=gender_text + "\n\n" + (update.message.caption or ""),
                message_thread_id=thread_id
            )
        elif update.message.video:
            sent_msg = await context.bot.send_video(
                chat_id=channel_id,
                video=update.message.video.file_id,
                caption=gender_text + "\n\n" + (update.message.caption or ""),
                message_thread_id=thread_id
            )
        else:
            await update.message.reply_text("Topik ini hanya menerima foto/video.")
            return

    elif topic in ["Moan Cwo","Moan Cwe"]:
        channel_id = CHANNEL_MAPPING[topic]
        if update.message.voice:
            sent_msg = await context.bot.send_voice(
                chat_id=channel_id,
                voice=update.message.voice.file_id,
                caption=gender_text + "\n\n" + (update.message.caption or ""),
                message_thread_id=thread_id
            )
        elif update.message.audio:
            sent_msg = await context.bot.send_audio(
                chat_id=channel_id,
                audio=update.message.audio.file_id,
                caption=gender_text + "\n\n" + (update.message.caption or ""),
                message_thread_id=thread_id
            )
        else:
            await update.message.reply_text("Topik ini hanya menerima voice/audio.")
            return

    else:
        await update.message.reply_text("Topik tidak dikenal.")
        return

    # Notifikasi admin
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin, text=f"[{topic}] Pesan baru dari user {user_id}.")
        except:
            pass

    await update.message.reply_text(f"✅ Pesan berhasil dikirim ke topik '{topic}'.")

    # Reaction keyboard
    if sent_msg:
        user_state[user_id]["last_message_id"] = sent_msg.message_id
        await add_reaction_keyboard(sent_msg, context)

# ================== REACTION ==================
async def add_reaction_keyboard(message, context):
    keyboard = [[InlineKeyboardButton(emoji, callback_data=f"react_{emoji}_{message.message_id}") for emoji in EMOJI_LIST]]
    await context.bot.send_message(chat_id=message.chat_id, text="React:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    emoji = data[1]
    msg_id = int(data[2])
    user_id = query.from_user.id

    if msg_id not in reaction_data:
        reaction_data[msg_id] = {e: set() for e in EMOJI_LIST}
    if user_id in reaction_data[msg_id][emoji]:
        reaction_data[msg_id][emoji].remove(user_id)
    else:
        reaction_data[msg_id][emoji].add(user_id)
    await query.message.edit_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton(f"{e} {len(reaction_data[msg_id][e])}", callback_data=f"react_{e}_{msg_id}") for e in EMOJI_LIST]])
    )

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handler
    app.add_handler(CommandHandler("start", start))

    # Callback handler
    app.add_handler(CallbackQueryHandler(gender_choice, pattern="^gender_"))
    app.add_handler(CallbackQueryHandler(topic_choice, pattern="^topic_"))
    app.add_handler(CallbackQueryHandler(hashtag_choice, pattern="^hashtag_"))
    app.add_handler(CallbackQueryHandler(lp_id_choice, pattern="^lp_"))
    app.add_handler(CallbackQueryHandler(handle_reaction, pattern="^react_"))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO, handle_message))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
