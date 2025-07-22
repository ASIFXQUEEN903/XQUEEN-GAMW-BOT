import os
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, InlineQueryHandler, ContextTypes
from uuid import uuid4

# Global game storage
GAMES = {}

# Constants
GRID_SIZE = 5
TOTAL_MINES = 5

# Create new game board
def create_game() -> dict:
    grid = [["⬜" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    mines = set()
    while len(mines) < TOTAL_MINES:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        mines.add((x, y))
    return {
        "grid": grid,
        "mines": mines,
        "revealed": set(),
        "over": False,
        "winner": None
    }

# Build clickable grid
def build_markup(game_id):
    game = GAMES[game_id]
    buttons = []
    for i in range(GRID_SIZE):
        row = []
        for j in range(GRID_SIZE):
            cell = game['grid'][i][j]
            row.append(InlineKeyboardButton(cell, callback_data=f"{game_id}:{i}:{j}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

# Handle clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user.first_name
    data = query.data
    game_id, x, y = data.split(":")
    x, y = int(x), int(y)
    game = GAMES.get(game_id)

    if not game or game['over']:
        await query.edit_message_text("❌ This game is over or invalid.")
        return

    if (x, y) in game['mines']:
        game['grid'][x][y] = "💥"
        game['over'] = True
        await query.edit_message_text(
            f"💣 BOOM! {user} clicked a mine!\n❌ LOSER: {user}",
            reply_markup=build_markup(game_id)
        )
        return

    game['grid'][x][y] = "✅"
    game['revealed'].add((x, y))

    if GRID_SIZE * GRID_SIZE - len(game['mines']) == len(game['revealed']):
        game['over'] = True
        game['winner'] = user
        await query.edit_message_text(
            f"🎉 All safe boxes opened!\n✅ WINNER: {user}",
            reply_markup=build_markup(game_id)
        )
        return

    await query.edit_message_reply_markup(reply_markup=build_markup(game_id))

# Start game via inline query
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    game_id = str(uuid4())[:8]
    GAMES[game_id] = create_game()

    result = [
        {
            "type": "article",
            "id": game_id,
            "title": "💣 Start Mines Game",
            "description": "Multiplayer minesweeper game. Click to play!",
            "input_message_content": {
                "message_text": f"🧨 XQueen Mines Game Started!\nClick a box and avoid the mine 💣"
            },
            "reply_markup": build_markup(game_id).to_dict()
        }
    ]
    await query.answer(result, cache_time=1)

# Start bot
if __name__ == '__main__':
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🎮 Inline Mines Game Bot running...")
    app.run_polling()
