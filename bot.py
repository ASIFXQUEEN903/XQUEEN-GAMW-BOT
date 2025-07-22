import os
import random
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes
from uuid import uuid4

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Heroku env se token

# Stylish font helper
def stylize(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    fancy = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ''.join(fancy[normal.index(c)] if c in normal else c for c in text)

# Game logic functions
def dice_game():
    number = random.randint(1, 6)
    return f"🎲 {stylize('You rolled a')} {number}!"

def coin_toss():
    result = random.choice(["🪙 Heads", "🪙 Tails"])
    return stylize(result)

def guess_number():
    correct = random.randint(1, 10)
    return f"🔢 {stylize('Guess a number between 1-10')} → {correct}"

def quiz_game():
    q = random.choice([
        ("What is the capital of India?", "Delhi"),
        ("5 + 7 = ?", "12"),
        ("Color of banana?", "Yellow"),
        ("Who wrote Ramayana?", "Valmiki")
    ])
    return f"❓ {stylize(q[0])}\n{stylize('Answer')}: {stylize(q[1])}"

def word_scramble():
    words = ["python", "telegram", "inline", "gamer", "india"]
    word = random.choice(words)
    scrambled = ''.join(random.sample(word, len(word)))
    return f"🔤 {stylize('Unscramble this')}: {scrambled}\n{stylize('Answer')}: {word}"

def rps_game():
    user = random.choice(["🪨 Rock", "📄 Paper", "✂️ Scissors"])
    bot = random.choice(["🪨 Rock", "📄 Paper", "✂️ Scissors"])
    result = "Draw" if user == bot else "You Win!" if (
        user == "🪨 Rock" and bot == "✂️ Scissors") or (
        user == "📄 Paper" and bot == "🪨 Rock") or (
        user == "✂️ Scissors" and bot == "📄 Paper") else "You Lose!"
    return f"🤖 {stylize('Bot chose')}: {bot}\n🙋 {stylize('You got')}: {user}\n🎮 {stylize(result)}"

# Inline query handler
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    results = []

    games = {
        "dice": dice_game,
        "coin": coin_toss,
        "guess": guess_number,
        "quiz": quiz_game,
        "scramble": word_scramble,
        "rps": rps_game
    }

    for key, func in games.items():
        if query in key or not query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=key.capitalize() + " Game",
                    description="Play " + key + " game",
                    input_message_content=InputTextMessageContent(func(), parse_mode="Markdown")
                )
            )

    await update.inline_query.answer(results[:10], cache_time=1)

# Start bot
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query_handler))
    print("🎮 Inline Game Bot is running...")
    app.run_polling()
