import logging
import random
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ==================== ØªÙ†Ø¸ÛŒÙ…Ø§Øª ====================
TOKEN = "8724613423:AAHMrCBnHfbA9TDy7cNtFmDhZQV4V_rLs40''
OWNER_ID = 8813403561  # Ø§Ø² @userinfobot Ø¨Ú¯ÛŒØ±

logging.basicConfig(level=logging.INFO)

GRID_ROWS = 4
GRID_COLS = 5
TOTAL_CELLS = GRID_ROWS * GRID_COLS
NUM_BOMBS = 5
NUM_SAFE = TOTAL_CELLS - NUM_BOMBS
MIN_BET = 1
USERS_FILE = "users.json"

# ==================== Ù…Ø¯ÛŒØ±ÛŒØª Ú©Ø§Ø±Ø¨Ø±Ø§Ù† ====================
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {"coins": 0}
        save_users(users)
    return users[user_id_str]

def update_user_coins(user_id, amount):
    users = load_users()
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {"coins": 0}
    users[user_id_str]["coins"] += amount
    save_users(users)

# ==================== ØªÙˆØ§Ø¨Ø¹ Ø¶Ø±ÛŒØ¨ ====================
def get_multiplier(n):
    multipliers = [1.0, 1.05, 1.1, 1.2, 1.5, 1.6, 2.0, 2.7, 3.6, 4.8, 7.0]
    return multipliers[n] if n < len(multipliers) else 7.0

# ==================== Ø³Ø§Ø®Øª Ú©ÛŒØ¨ÙˆØ±Ø¯ Ø¨Ø§Ø²ÛŒ ====================
def build_game_keyboard(game_data, game_over=False):
    bombs = game_data["bombs"]
    revealed = game_data["revealed"]
    bet = game_data["bet"]
    safe_count = len(revealed)
    current_multiplier = get_multiplier(safe_count)
    next_multiplier = get_multiplier(safe_count + 1)
    
    keyboard = []
    for row in range(GRID_ROWS):
        row_buttons = []
        for col in range(GRID_COLS):
            cell_id = row * GRID_COLS + col
            if game_over:
                if cell_id in bombs:
                    text = "ðŸ’£"
                elif cell_id in revealed:
                    text = "âœ…"
                else:
                    text = "â¬›"
                row_buttons.append(InlineKeyboardButton(text, callback_data="ignore"))
            else:
                if cell_id in revealed:
                    row_buttons.append(InlineKeyboardButton("âœ…", callback_data="ignore"))
                else:
                    row_buttons.append(InlineKeyboardButton("â“", callback_data=f"open_{cell_id}"))
        keyboard.append(row_buttons)

    if not game_over:
        cashout_amount = bet * current_multiplier
        keyboard.append([InlineKeyboardButton(f"ðŸ’° Ø¨Ø±Ø¯Ø§Ø´Øª {cashout_amount:.2f}", callback_data="cashout")])
        keyboard.append([InlineKeyboardButton(f"â© Ø¨Ø¹Ø¯ÛŒ {next_multiplier:.2f}", callback_data="next_show")])
    else:
        keyboard.append([InlineKeyboardButton("ðŸ  Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# ==================== Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ ====================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    coins = get_user(user_id)["coins"]
    
    text = (
        "ðŸŒ¹ **Ø®ÙˆØ´ Ø§ÙˆÙ…Ø¯ÛŒØ¯ Ø¨Ù‡ Ø¨Ù…Ø¨ Ù‡Ø§Ø¨**\n"
        "Ø±ÛŒØ³Ú© Ø§Ø² Ø´Ù…Ø§ØŒ Ø³ÙˆØ¯ Ø§Ø² Ù…Ø§ âœ…\n\n"
        f"ðŸ’° Ù…ÙˆØ¬ÙˆØ¯ÛŒ Ø´Ù…Ø§: {coins} Ú©ÙˆÛŒÙ†\n"
        "Ø¨Ø±Ø§ÛŒ Ø´Ø±ÙˆØ¹ Ø¨Ø§Ø²ÛŒØŒ Ø¯Ú©Ù…Ù‡ Ø²ÛŒØ± Ø±Ø§ Ø¨Ø²Ù†ÛŒØ¯:"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ’° Ù…Ø§ÛŒÙ†Ø²", callback_data="start_game")]])
    
    if query:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ==================== Ø´Ø±ÙˆØ¹ Ø¨Ø§Ø²ÛŒ ====================
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    coins = get_user(user_id)["coins"]
    
    if coins < MIN_BET:
        await query.edit_message_text(
            f"âŒ Ø´Ù…Ø§ Ú©ÙˆÛŒÙ† Ù„Ø§Ø²Ù… Ø¨Ø±Ø§ÛŒ Ø¨Ø§Ø²ÛŒ Ø±Ùˆ Ù†Ø¯Ø§Ø±ÛŒØ¯.\nØ­Ø¯Ø§Ù‚Ù„ Ø´Ø±Ø· {MIN_BET} Ú©ÙˆÛŒÙ† Ø§Ø³Øª.\nÙ…ÙˆØ¬ÙˆØ¯ÛŒ Ø´Ù…Ø§: {coins} Ú©ÙˆÛŒÙ†",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ  Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )
        return
    
    context.user_data["state"] = "WAITING_BET"
    await query.edit_message_text(
        f"ðŸ’° Ù…Ø¨Ù„Øº Ø¨Ø§Ø²ÛŒ Ø±Ùˆ Ø§Ù†ØªØ®Ø§Ø¨ Ú©Ù†ÛŒØ¯ ðŸ›‘\nØ­Ø¯Ø§Ù‚Ù„ Ù…Ø¨Ù„Øº {MIN_BET} Ú©ÙˆÛŒÙ† ðŸ’²\nÙ…ÙˆØ¬ÙˆØ¯ÛŒ Ø´Ù…Ø§: {coins} Ú©ÙˆÛŒÙ†\n\nÙ„Ø·ÙØ§Ù‹ ÛŒÚ© Ø¹Ø¯Ø¯ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯:",
        parse_mode="Markdown"
    )

# ==================== Ø¯Ø±ÛŒØ§ÙØª Ù…Ø¨Ù„Øº Ø´Ø±Ø· ====================
async def handle_bet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") != "WAITING_BET":
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not text.isdigit():
        await update.message.reply_text("âŒ Ù„Ø·ÙØ§Ù‹ ÙÙ‚Ø· ÛŒÚ© Ø¹Ø¯Ø¯ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯.")
        return
    
    bet_amount = int(text)
    if bet_amount < MIN_BET:
        await update.message.reply_text(f"âŒ Ø­Ø¯Ø§Ù‚Ù„ Ù…Ø¨Ù„Øº {MIN_BET} Ú©ÙˆÛŒÙ† Ø§Ø³Øª.")
        return
    
    user_data = get_user(user_id)
    if user_data["coins"] < bet_amount:
        await update.message.reply_text(
            f"âŒ Ù…ÙˆØ¬ÙˆØ¯ÛŒ Ø´Ù…Ø§ Ú©Ø§ÙÛŒ Ù†ÛŒØ³Øª.\nÙ…ÙˆØ¬ÙˆØ¯ÛŒ: {user_data['coins']} Ú©ÙˆÛŒÙ†",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ  Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ", callback_data="main_menu")]])
        )
        return
    
    update_user_coins(user_id, -bet_amount)
    
    bomb_positions = set(random.sample(range(TOTAL_CELLS), NUM_BOMBS))
    game_data = {
        "bombs": bomb_positions,
        "revealed": set(),
        "bet": bet_amount,
        "game_over": False
    }
    context.user_data["game"] = game_data
    context.user_data["state"] = "PLAYING"
    
    text = (
        f"ðŸ’£ **Ø¨Ø§Ø²ÛŒ Ø´Ø±ÙˆØ¹ Ø´Ø¯!**\n"
        f"ðŸ’° Ø´Ø±Ø·: {bet_amount} Ú©ÙˆÛŒÙ†\n"
        f"â­ Ø¶Ø±ÛŒØ¨ ÙØ¹Ù„ÛŒ: {get_multiplier(0):.2f}\n"
        f"ðŸŽ¯ {NUM_SAFE} Ø®Ø§Ù†Ù‡ Ø§Ù…Ù† Ù¾ÛŒØ¯Ø§ Ú©Ù†!\n\n"
        "Ø±ÙˆÛŒ â“ Ú©Ù„ÛŒÚ© Ú©Ù†."
    )
    keyboard = build_game_keyboard(game_data)
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ==================== Ù…Ø¯ÛŒØ±ÛŒØª Ú©Ù„ÛŒÚ©â€ŒÙ‡Ø§ÛŒ Ø¨Ø§Ø²ÛŒ ====================
async def handle_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "main_menu":
        await main_menu(update, context)
        return
    
    if data == "start_game":
        await start_game(update, context)
        return
    
    if data in ["ignore", "next_show"]:
        return
    
    game_data = context.user_data.get("game")
    if not game_data or game_data.get("game_over"):
        await query.edit_message_text("â³ Ø¨Ø§Ø²ÛŒ ØªÙ…Ø§Ù… Ø´Ø¯Ù‡.")
        return
    
    if data == "cashout":
        safe_count = len(game_data["revealed"])
        multiplier = get_multiplier(safe_count)
        cashout_amount = game_data["bet"] * multiplier
        update_user_coins(user_id, cashout_amount)
        game_data["game_over"] = True
        text = (
            f"ðŸ’° **Ø¨Ø±Ø¯Ø§Ø´Øª Ù…ÙˆÙÙ‚!**\n"
            f"Ø¶Ø±ÛŒØ¨: {multiplier:.2f}\n"
            f"Ù…Ø¨Ù„Øº: {cashout_amount:.2f} Ú©ÙˆÛŒÙ†\n"
            f"Ù…ÙˆØ¬ÙˆØ¯ÛŒ Ø¬Ø¯ÛŒØ¯: {get_user(user_id)['coins']} Ú©ÙˆÛŒÙ†"
        )
        keyboard = build_game_keyboard(game_data, game_over=True)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    if data.startswith("open_"):
        cell_id = int(data.split("_")[1])
        bombs = game_data["bombs"]
        revealed = game_data["revealed"]
        
        if cell_id in revealed:
            return
        
        if cell_id in bombs:
            game_data["game_over"] = True
            text = f"ðŸ’¥ **Ø¨Ø§Ø®ØªÛŒ!**\nÙ…Ø¨Ù„Øº Ø´Ø±Ø·: {game_data['bet']} Ú©ÙˆÛŒÙ† Ø§Ø² Ø¯Ø³Øª Ø±ÙØª."
            keyboard = build_game_keyboard(game_data, game_over=True)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        revealed.add(cell_id)
        safe_count = len(revealed)
        
        if safe_count == NUM_SAFE:
            game_data["game_over"] = True
            multiplier = get_multiplier(safe_count)
            win_amount = game_data["bet"] * multiplier
            update_user_coins(user_id, win_amount)
            text = (
                f"ðŸŽ‰ **ØªØ¨Ø±ÛŒÚ©! Ø¨Ø±Ù†Ø¯Ù‡ Ø´Ø¯ÛŒ!**\n"
                f"Ø¶Ø±ÛŒØ¨: {multiplier:.2f}\n"
                f"Ø¬Ø§ÛŒØ²Ù‡: {win_amount:.2f} Ú©ÙˆÛŒÙ†\n"
                f"Ù…ÙˆØ¬ÙˆØ¯ÛŒ Ø¬Ø¯ÛŒØ¯: {get_user(user_id)['coins']} Ú©ÙˆÛŒÙ†"
            )
            keyboard = build_game_keyboard(game_data, game_over=True)
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        current_multiplier = get_multiplier(safe_count)
        next_multiplier = get_multiplier(safe_count + 1)
        cashout_amount = game_data["bet"] * current_multiplier
        
        text = (
            f"ðŸ’£ **Ø¨Ø§Ø²ÛŒ Ø§Ø¯Ø§Ù…Ù‡ Ø¯Ø§Ø±Ø¯**\n"
            f"â­ Ø¶Ø±ÛŒØ¨ ÙØ¹Ù„ÛŒ: {current_multiplier:.2f}\n"
            f"â© Ø¶Ø±ÛŒØ¨ Ø¨Ø¹Ø¯ÛŒ: {next_multiplier:.2f}\n"
            f"ðŸŽ¯ {NUM_SAFE - safe_count} Ø®Ø§Ù†Ù‡ Ø¨Ø§Ù‚ÛŒâ€ŒÙ…Ø§Ù†Ø¯Ù‡\n"
            f"ðŸ’° Ù‚Ø§Ø¨Ù„ Ø¨Ø±Ø¯Ø§Ø´Øª: {cashout_amount:.2f} Ú©ÙˆÛŒÙ†"
        )
        keyboard = build_game_keyboard(game_data)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ==================== Ø¯Ø³ØªÙˆØ± Ø§ÙØ²Ø§ÛŒØ´ Ú©ÙˆÛŒÙ† (ÙÙ‚Ø· Ù…Ø§Ù„Ú©) ====================
async def add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("â›” Ø´Ù…Ø§ Ø¯Ø³ØªØ±Ø³ÛŒ Ù†Ø¯Ø§Ø±ÛŒØ¯.")
        return
    
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("âŒ ÙØ±Ù…Øª: /addcoins [ØªØ¹Ø¯Ø§Ø¯] [Ø¢ÛŒØ¯ÛŒ]")
        return
    
    try:
        amount = int(args[0])
        target_id = int(args[1])
    except ValueError:
        await update.message.reply_text("âŒ Ø§Ø¹Ø¯Ø§Ø¯ Ù…Ø¹ØªØ¨Ø± ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯.")
        return
    
    update_user_coins(target_id, amount)
    await update.message.reply_text(f"âœ… {amount} Ú©ÙˆÛŒÙ† Ø¨Ù‡ Ú©Ø§Ø±Ø¨Ø± {target_id} Ø§Ø¶Ø§ÙÙ‡ Ø´Ø¯.")

# ==================== Ø¯Ø³ØªÙˆØ± start ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

# ==================== Ø§Ø¬Ø±Ø§ÛŒ Ø§ØµÙ„ÛŒ ====================
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcoins", add_coins))
    app.add_handler(CommandHandler("menu", start))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_game, pattern="^start_game$")],
        states={
            "WAITING_BET": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bet_input)],
        },
        fallbacks=[CommandHandler("menu", start)],
        allow_reentry=True
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_game_callback, pattern="^(open_|cashout|main_menu|next_show|start_game|ignore)"))
    
    print("ðŸ¤– Ø±Ø¨Ø§Øª Ù…Ø§ÛŒÙ†â€ŒÛŒØ§Ø¨ Ø¨Ø§ Ø³ÛŒØ³ØªÙ… Ú©ÙˆÛŒÙ† Ø±ÙˆØ´Ù† Ø´Ø¯...")
    app.run_polling()

if __name__ == "__main__":
    main()