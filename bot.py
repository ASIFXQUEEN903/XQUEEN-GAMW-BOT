import os
import random
import asyncio
from uuid import uuid4
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    Update, InputTextMessageContent, InlineQueryResultArticle
)
from telegram.ext import (
    Application, CallbackQueryHandler,
    InlineQueryHandler, ContextTypes,
    CommandHandler
)

# --------------------
# GAME STORAGE
# --------------------
GAMES = {}
RPS_PLAYERS = {}

GRID_SIZE = 5
TOTAL_MINES = 5
GAME_DURATION = 120  # seconds

# --------------------
# STYLISH TEXT
# --------------------
def stylize(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    fancy = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ''.join(fancy[normal.index(c)] if c in normal else c for c in text)

# --------------------
# MINES GAME
# --------------------
def create_mines_game():
    grid = [["⬜" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    mines = set()
    while len(mines) < TOTAL_MINES:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        mines.add((x, y))
    return {
        "grid": grid,
        "mines": mines,
        "revealed": set(),
        "flags": set(),
        "over": False,
        "winner": None,
        "start_time": asyncio.get_event_loop().time()
    }

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user.first_name
    data = query.data
    game_id, x, y = data.split(":")
    x, y = int(x), int(y)
    game = GAMES.get(game_id)

    if not game:
        await query.edit_message_text("❌ Game not found.")
        return

    now = asyncio.get_event_loop().time()
    if game['over'] or (now - game['start_time'] > GAME_DURATION):
        game['over'] = True
        await query.edit_message_text("⏱ Game Over! Time expired.", reply_markup=build_markup(game_id))
        return

    if (x, y) in game['revealed']:
        return

    if (x, y) in game['mines']:
        game['grid'][x][y] = "💥"
        game['over'] = True
        await query.edit_message_text(f"💣 BOOM! {user} clicked a mine!\n❌ LOSER: {user}", reply_markup=build_markup(game_id))
        return

    game['grid'][x][y] = "✅"
    game['revealed'].add((x, y))

    remaining = GRID_SIZE * GRID_SIZE - len(game['mines']) - len(game['revealed'])
    if remaining == 0:
        game['over'] = True
        game['winner'] = user
        await query.edit_message_text(f"🎉 All safe boxes opened!\n🥇 WINNER: {user}", reply_markup=build_markup(game_id))
        return

    await query.edit_message_reply_markup(reply_markup=build_markup(game_id))

# --------------------
# RPS GAME
# --------------------
async def rps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text("Use this command in a group to challenge others!")
        return

    group_id = str(update.message.chat_id)
    if group_id in RPS_PLAYERS:
        await update.message.reply_text("⚠️ A RPS match is already active in this group!")
        return

    RPS_PLAYERS[group_id] = {}
    buttons = [
        [InlineKeyboardButton("🪨 Rock", callback_data="rps:rock"),
         InlineKeyboardButton("📄 Paper", callback_data="rps:paper"),
         InlineKeyboardButton("✂️ Scissors", callback_data="rps:scissors")]
    ]
    await update.message.reply_text(
        "🎮 Rock Paper Scissors started! Click your choice:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def rps_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    group_id = str(query.message.chat_id)
    choice = query.data.split(":")[1]

    if group_id not in RPS_PLAYERS:
        await query.edit_message_text("❌ This RPS session expired or not started.")
        return

    RPS_PLAYERS[group_id][user_id] = (user_name, choice)
    selected = len(RPS_PLAYERS[group_id])

    if selected >= 2:
        players = list(RPS_PLAYERS[group_id].values())
        result_text = "\n".join([f"{u} → {c}" for u, c in players])
        winner = evaluate_rps(players)
        if winner:
            result_text += f"\n\n🏆 {stylize(winner)} wins!"
        else:
            result_text += "\n\n🤝 It's a draw!"
        await query.edit_message_text(f"🎮 RPS Result:\n{result_text}")
        del RPS_PLAYERS[group_id]
    else:
        await query.edit_message_text("✅ 1 player selected. Waiting for more...")

def evaluate_rps(players):
    choices = {p[1] for p in players}
    if len(choices) == 1 or len(choices) == 3:
        return None  # Draw

    wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    for name1, c1 in players:
        if all(wins[c1] == c2 for _, c2 in players if c1 != c2):
            return name1
    return None

async def cancel_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = str(update.message.chat_id)
    if group_id in RPS_PLAYERS:
        del RPS_PLAYERS[group_id]
        await update.message.reply_text("❌ RPS game cancelled.")
    else:
        await update.message.reply_text("⚠️ No active RPS game to cancel.")

# --------------------
# INLINE QUERY HANDLER
# --------------------
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    results = []

    if "mines" in query or not query:
        game_id = str(uuid4())[:8]
        GAMES[game_id] = create_mines_game()
        results.append(
            InlineQueryResultArticle(
                id=game_id,
                title="💣 Mines Game",
                description="Click & avoid the mine!",
                input_message_content=InputTextMessageContent(
                    "🧨 XQueen Mines Game Started! Avoid the mine 💣\n🕒 Auto end in 2 minutes."
                ),
                reply_markup=build_markup(game_id)
            )
        )

    await update.inline_query.answer(results[:10], cache_time=1)

# --------------------
# START BOT
# --------------------
if __name__ == "__main__":
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^.*:\d+:\d+$"))
    app.add_handler(CallbackQueryHandler(rps_click_handler, pattern=r"^rps:"))
    app.add_handler(CommandHandler("rps", rps_command))
    app.add_handler(CommandHandler("cancelrps", cancel_rps))

    print("🎮 XQueen Inline Game Bot is running...")
    app.run_polling()
