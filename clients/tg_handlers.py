from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, Application

SUPERVISOR_API_URL = str(settings.supervisor_api_url).rstrip("/")

async def forward_to_supervisor(prompt: str, session_id: str = None, user_id: str = None) -> str:
    url = f"{SUPERVISOR_API_URL}/supervisor/execute"
    payload = {"prompt": prompt}
    if session_id:
        payload["session_id"] = session_id
    if user_id:
        payload["user_id"] = user_id
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "[No response from supervisor]")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = str(update.effective_user.id) if update.effective_user else None
    session_id = str(update.effective_chat.id) if update.effective_chat else None
    prompt = update.message.text
    try:
        supervisor_response = await forward_to_supervisor(prompt, session_id=session_id, user_id=user_id)
    except Exception as e:
        await update.message.reply_text(f"Error contacting supervisor: {e}")
        return
    await update.message.reply_text(supervisor_response)

def register_handlers(application: Application) -> None:
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) 