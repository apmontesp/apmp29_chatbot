# =====================================================
# BOT DE TELEGRAM + GROQ LLM + TURSO
# Taller Ciencia de Datos -- EAFIT 2026
# =====================================================
import os, asyncio, datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler,
                           MessageHandler, filters, ContextTypes)
from groq import Groq
import libsql_client

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
TURSO_URL      = os.getenv("TURSO_URL")
TURSO_TOKEN    = os.getenv("TURSO_TOKEN")

# Debug temporal
print(f"TOKEN: {TELEGRAM_TOKEN[:10] if TELEGRAM_TOKEN else 'NONE'}")
print(f"GROQ: {GROQ_API_KEY[:10] if GROQ_API_KEY else 'NONE'}")
print(f"TURSO_URL: {TURSO_URL or 'NONE'}")
print(f"TURSO_TOKEN: {TURSO_TOKEN[:10] if TURSO_TOKEN else 'NONE'}")

groq_key = os.getenv("GROQ_API_KEY", "").strip()
cliente_groq = Groq(api_key=groq_key)

# ── Base de datos ──────────────────────────────────
async def inicializar_db():
    async with libsql_client.create_client(
        url=TURSO_URL, auth_token=TURSO_TOKEN) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT, usuario TEXT, user_id INTEGER,
                pregunta TEXT, respuesta TEXT, tokens INTEGER
            )""")

async def guardar_mensaje(usuario, user_id, pregunta, respuesta, tokens):
    fecha = datetime.datetime.now().isoformat()
    async with libsql_client.create_client(
        url=TURSO_URL, auth_token=TURSO_TOKEN) as db:
        await db.execute(
            "INSERT INTO mensajes (fecha, usuario, user_id, pregunta, respuesta, tokens) VALUES (?,?,?,?,?,?)",
            [fecha, usuario, user_id, pregunta, respuesta, tokens])

# ── LLM ───────────────────────────────────────────
def consultar_llm(pregunta):
    resp = cliente_groq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content":
                "Eres un asistente experto en ciencia de datos. "
                "Responde en español, claro y conciso."},
            {"role": "user", "content": pregunta}
        ],
        max_tokens=500, temperature=0.7)
    return (resp.choices[0].message.content,
            resp.usage.total_tokens)

# ── Handlers ──────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    await update.message.reply_text(
        f"¡Hola {nombre}! 🤖\n"
        "Soy tu asistente de ciencia de datos.\n"
        "Escríbeme cualquier pregunta.\n\n"
        "/ayuda - Ver instrucciones")

async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Puedo responder sobre:\n"
        "• Ciencia de datos\n"
        "• Machine learning\n"
        "• Visualización de datos\n"
        "• IA generativa")

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user.first_name or "Desconocido"
    user_id = update.effective_user.id
    pregunta = update.message.text
    await update.message.reply_text("Pensando... 🧠")
    try:
        respuesta, tokens = consultar_llm(pregunta)
        await guardar_mensaje(usuario, user_id, pregunta, respuesta, tokens)
        await update.message.reply_text(respuesta)
    except Exception as e:
        await update.message.reply_text("Tuve un problema. Intenta de nuevo.")
        print(f"Error: {e}")

# ── Main ──────────────────────────────────────────
async def main():
    await inicializar_db()
    print("Base de datos lista.")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    print("Bot iniciado. Esperando mensajes...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
