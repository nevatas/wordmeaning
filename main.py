import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

import database
import ai_client
import spaced_repetition

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    database.add_user(user_id)
    await update.message.reply_text(
        "Welcome! Send me any word to get a definition and add it to your learning list.\n"
        "Use /train to start a spaced repetition session."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    word = update.message.text.strip()
    
    if word.startswith('/'):
        return

    await update.message.reply_text(f"🔍 Defining '{word}'...")
    
    definition_text = ai_client.get_definition(word)
    
    # Save to DB
    database.add_word(user_id, word, definition_text, datetime.now())
    
    # Use Markdown escape for safety or just standard text.
    # We will use simple formatting.
    response = f"📖 *{word}*\n\n{definition_text}\n\n_Word saved to library._"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def train(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    due_words = database.get_due_words(user_id)
    
    if not due_words:
        msg = "🎉 Все слова изучены! На сегодня это все. Приходите завтра! 🧠"
        if update.callback_query:
            await update.callback_query.message.edit_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    # Pick the first one
    word_row = due_words[0]
    word_id = word_row['id']
    word = word_row['word']
    
    # Show ONLY the word first
    keyboard = [
        [
            InlineKeyboardButton("✅ I know it", callback_data=f"know_{word_id}"),
            InlineKeyboardButton("❌ I forgot", callback_data=f"forgot_{word_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"📝 **Review**: {word}"
    
    if update.callback_query:
        # If we are coming from a "Next" button or previous card
        await update.callback_query.message.edit_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("next_"):
        # Just trigger train() again
        await train(update, context)
        return

    action, word_id_str = data.split('_')
    word_id = int(word_id_str)
    
    word_row = database.get_word(word_id)
    if not word_row:
        await query.message.edit_text("Error: Word not found.")
        return

    current_level = word_row['repetition_level']
    
    if action == "know":
        # Mark correct, move to next immediately (or show brief success? User said "If forgot -> show definition". Implies know -> just go next)
        new_level, next_review = spaced_repetition.calculate_next_review(current_level, is_correct=True)
        database.update_word_progress(word_id, new_level, next_review)
        
        # Trigger next word
        await train(update, context)
        
    elif action == "forgot":
        # Mark incorrect
        new_level, next_review = spaced_repetition.calculate_next_review(current_level, is_correct=False)
        database.update_word_progress(word_id, new_level, next_review)
        
        # Show definition and "Next" button
        definition = word_row['definition']
        
        keyboard = [
            [InlineKeyboardButton("➡️ Next", callback_data=f"next_{word_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"📝 **Review**: {word_row['word']}\n\n❌ **Forgot**\n\n{definition}"
        
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=reply_markup)



if __name__ == '__main__':
    # Initialize DB
    database.init_db()
    
    # Build App
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        exit(1)
        
    application = ApplicationBuilder().token(token).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    train_handler = CommandHandler('train', train)
    callback_handler = CallbackQueryHandler(button)
    
    application.add_handler(start_handler)
    application.add_handler(train_handler)
    application.add_handler(callback_handler)
    application.add_handler(message_handler) 
    
    print("Bot is running...")
    application.run_polling()
