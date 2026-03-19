import os
from dotenv import load_dotenv
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

cliente_groq = Groq(api_key=GROQ_API_KEY)

def consultar_llm(pregunta: str) -> tuple[str, int]:
    """Envía la pregunta a Groq y devuelve respuesta y tokens usados."""
    respuesta = cliente_groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "Eres un asistente inteligente de EAFIT. Responde siempre en español."},
            {"role": "user", "content": pregunta}
        ]
    )
    texto = respuesta.choices[0].message.content
    tokens = respuesta.usage.total_tokens
    return texto, tokens

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu asistente de EAFIT 🤖\nEscríbeme cualquier pregunta.")

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = update.message.text
    await update.message.reply_text("Pensando... 🧠")
    
    try:
        respuesta, tokens = consultar_llm(pregunta)
        await update.message.reply_text(f"{respuesta}\n\n_Tokens usados: {tokens}_", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot corriendo...")
    app.run_polling()
