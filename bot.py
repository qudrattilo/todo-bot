# bot.py
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)
import config
import database
import asyncio
from datetime import datetime, timedelta

# -------------------------------------------------
# Database yaratish
database.init_db()

# -------------------------------------------------
# O‘zbekcha tugmalar
def get_main_menu():
    keyboard = [
        ["➕ Vazifa qo‘shish", "📋 Vazifalar ro‘yxati"],
        ["✅ Bajarildi", "⏰ Esdalatma"],
        ["💡 Motivatsiya", "📊 Statistika"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# -------------------------------------------------
# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men – *Kunlik Rejalashtiruvchi Bot* 🤖\n\n"
        "📌 Tugmalar orqali ishlating:\n"
        "   • *Vazifa qo‘shish* → yozing\n"
        "   • *Bajarildi* → raqam kiriting\n"
        "   • *Esdalatma* → vaqt + xabar\n",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

# -------------------------------------------------
# /add (buyruq orqali)
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "❌ Vazifa yozing: /add Kitob o‘qish",
            reply_markup=get_main_menu()
        )
        return
    task = " ".join(context.args)
    database.add_task(user_id, task)
    await update.message.reply_text(
        f"✅ *Qo'shildi:* {task}",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

# -------------------------------------------------
# Matndan vazifa qo‘shish (tugma → “Vazifa qo‘shish”)
async def add_task_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = update.message.text.strip()
    if not task:
        await update.message.reply_text(
            "❌ Bo‘sh vazifa qo‘shib bo‘lmaydi!",
            reply_markup=get_main_menu()
        )
        return
    database.add_task(user_id, task)
    await update.message.reply_text(
        f"✅ *Qo'shildi:* {task}",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

# -------------------------------------------------
# /list
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = database.get_tasks(user_id)
    if not tasks:
        await update.message.reply_text(
            "📭 Hozircha vazifa yo‘q. /add bilan qo‘shing!",
            reply_markup=get_main_menu()
        )
        return

    msg = "*Vazifalar:*\n\n"
    for idx, (task_id, task, done) in enumerate(tasks, 1):
        status = "✅" if done else "⏳"
        msg += f"{status} {idx}. {task}  `(/done {task_id})`\n"
    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

# -------------------------------------------------
# /done (buyruq orqali)
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "❌ Raqam yozing: /done 1",
            reply_markup=get_main_menu()
        )
        return
    try:
        task_id = int(context.args[0])
        if database.complete_task(task_id, user_id):
            await update.message.reply_text(
                "✅ *Bajarildi!*",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "❌ Vazifa topilmadi yoki sizniki emas.",
                reply_markup=get_main_menu()
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Raqam kiriting!",
            reply_markup=get_main_menu()
        )

# -------------------------------------------------
# Matndan done (tugma → “Bajarildi”)
async def done_task_from_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        task_id = int(text)
        if database.complete_task(task_id, user_id):
            await update.message.reply_text(
                "✅ *Bajarildi!*",
                parse_mode='Markdown',
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "❌ Vazifa topilmadi yoki sizniki emas.",
                reply_markup=get_main_menu()
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Faqat raqam kiriting! Masalan: 1",
            reply_markup=get_main_menu()
        )

# -------------------------------------------------
# /remind
async def remind_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Masalan: /remind 15:30 Dars boshlanadi",
            reply_markup=get_main_menu()
        )
        return

    time_str = context.args[0]
    message = " ".join(context.args[1:])

    try:
        h, m = map(int, time_str.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
    except:
        await update.message.reply_text(
            "❌ Vaqt: HH:MM (15:30)",
            reply_markup=get_main_menu()
        )
        return

    now = datetime.now()
    remind_time = datetime(now.year, now.month, now.day, h, m)
    if remind_time < now:
        remind_time += timedelta(days=1)

    delay = (remind_time - now).total_seconds()
    await update.message.reply_text(
        f"⏰ *Esdalatma:* {time_str} → {message}",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

    await asyncio.sleep(delay)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🔔 *ESDALATMA!*\n{message}",
        parse_mode='Markdown'
    )

# -------------------------------------------------
# /motiv
async def motiv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = [
        "Har bir kun – yangi imkoniyat!",
        "Kichik qadamlar katta natijalarga olib boradi.",
        "Muvaffaqiyat – har kuni harakat qilishda.",
        "Siz qobiliyatlisiz!"
    ]
    import random
    await update.message.reply_text(
        f"💡 *Motivatsiya:*\n_{random.choice(quotes)}_",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

# -------------------------------------------------
# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = database.get_tasks(user_id)
    total = len(tasks)
    done = sum(1 for _, _, d in tasks if d)
    pending = total - done

    msg = f"📊 *Statistika:*\n\n"
    msg += f"Umumiy: {total}\n"
    msg += f"Bajarilgan: {done} ✅\n"
    msg += f"Kutilmoqda: {pending} ⏳\n"

    if total > 0:
        progress = int((done / total) * 100)
        bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        msg += f"\nNatija: {progress}% {bar}"

    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

# -------------------------------------------------
# Tugma bosilganda matnni qayta ishlash
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ---- Tugmalar ----
    if text == "➕ Vazifa qo‘shish":
        await update.message.reply_text(
            "Yangi vazifa yozing:\nMasalan: *Kitob o‘qish*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_task'] = True
        return

    if text == "📋 Vazifalar ro‘yxati":
        await list_tasks(update, context)
        return

    if text == "✅ Bajarildi":
        await update.message.reply_text(
            "Bajarilgan vazifa raqamini yozing:\nMasalan: *1*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_done'] = True
        return

    if text == "⏰ Esdalatma":
        await update.message.reply_text(
            "Vaqt va xabarni yozing:\nMasalan: */remind 15:30 Uchrashuv*",
            parse_mode='Markdown'
        )
        return

    if text == "💡 Motivatsiya":
        await motiv(update, context)
        return

    if text == "📊 Statistika":
        await stats(update, context)
        return

    # ---- Vazifa kiritish holati ----
    if context.user_data.get('waiting_for_task'):
        await add_task_from_text(update, context)
        context.user_data['waiting_for_task'] = False
        return

    # ---- Done kiritish holati ----
    if context.user_data.get('waiting_for_done'):
        await done_task_from_text(update, context)
        context.user_data['waiting_for_done'] = False
        return

# -------------------------------------------------
# Main
def main():
    app = Application.builder().token(config.TOKEN).build()

    # Buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("remind", remind_task))
    app.add_handler(CommandHandler("motiv", motiv))
    app.add_handler(CommandHandler("stats", stats))

    # Tugma matnlari
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot ishga tushdi... (Ctrl+C to‘xtatish)")
    app.run_polling()

if __name__ == '__main__':
    main()
