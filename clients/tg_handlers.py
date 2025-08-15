from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, Application, CommandHandler, CallbackQueryHandler
from services.image.image_service import ImageService
from utils.config import get_settings
from utils.constants import IMAGE_API
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
settings = get_settings()

SUPERVISOR_API_URL = str(settings.supervisor_api_url).rstrip("/")

# Initialize ImageService
image_service = ImageService(
    api_key=settings.image_router_api_key,
    base_url=IMAGE_API
)

# Store user image generation sessions
user_sessions: Dict[str, Dict[str, Any]] = {}

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

async def handle_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /img command for image generation with interactive UI.
    
    This creates a step-by-step process where users can:
    1. Enter their prompt
    2. Select a model from available options
    3. Choose size and quality settings
    4. Generate the image
    """
    if not update.message or not update.message.text:
        return
    
    # Parse command arguments
    command_parts = update.message.text.split()
    
    if len(command_parts) < 2:
        # Show help message
        help_text = """🎨 *Image Generation Command*

*Usage:* `/img <prompt>`

*Examples:*
• `/img a beautiful sunset`
• `/img a cat playing with yarn`
• `/img portrait of a robot`

After entering your prompt, you'll be guided through:
1. Model selection
2. Size and quality settings
3. Image generation

*Available Models:*
• `sdxl` - Fast generation, good quality
• `inf` - InfiniteYou model  
• `chroma` - Chroma model
• `test` - Test model

*Available Sizes:*
• `256x256`, `512x512`, `1024x1024`
• `1792x1024`, `1024x1792`

*Available Qualities:*
• `auto`, `low`, `medium`, `high`"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    # Extract prompt
    prompt = command_parts[1]
    
    # Create user session
    user_id = str(update.effective_user.id)
    session_id = f"img_{user_id}_{update.effective_chat.id}"
    
    user_sessions[session_id] = {
        "prompt": prompt,
        "model": None,
        "size": None,
        "quality": None,
        "step": "model_selection"
    }
    
    # Show model selection
    await show_model_selection(update, context, session_id)

async def show_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: str) -> None:
    """Show model selection buttons."""
    session = user_sessions.get(session_id)
    if not session:
        await update.message.reply_text("❌ Session expired. Please use /img again.")
        return
    
    prompt = session["prompt"]
    models = image_service.get_supported_models()
    
    # Create model selection buttons
    keyboard = []
    for model in models:
        # Extract model name for display
        model_display = model.split('/')[-1].replace('-', ' ').title()
        keyboard.append([InlineKeyboardButton(
            model_display, 
            callback_data=f"model:{session_id}:{model}"
        )])
    
    # Add cancel button
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{session_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎨 *Image Generation Setup*\n\n"
        f"*Prompt:* {prompt}\n\n"
        f"*Step 1: Select a model*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: str) -> None:
    """Show size selection buttons."""
    session = user_sessions.get(session_id)
    if not session:
        return
    
    prompt = session["prompt"]
    model = session["model"]
    
    sizes = image_service.get_supported_sizes()
    
    # Create size selection buttons
    keyboard = []
    for size in sizes:
        keyboard.append([InlineKeyboardButton(
            size, 
            callback_data=f"size:{session_id}:{size}"
        )])
    
    # Add back and cancel buttons
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data=f"back_model:{session_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{session_id}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the message to show size selection
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"🎨 *Image Generation Setup*\n\n"
            f"*Prompt:* {prompt}\n"
            f"*Model:* {model}\n\n"
            f"*Step 2: Select image size*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_quality_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: str) -> None:
    """Show quality selection buttons."""
    session = user_sessions.get(session_id)
    if not session:
        return
    
    prompt = session["prompt"]
    model = session["model"]
    size = session["size"]
    
    qualities = image_service.get_supported_qualities()
    
    # Create quality selection buttons
    keyboard = []
    for quality in qualities:
        quality_display = quality.title()
        keyboard.append([InlineKeyboardButton(
            quality_display, 
            callback_data=f"quality:{session_id}:{quality}"
        )])
    
    # Add back and cancel buttons
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data=f"back_size:{session_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{session_id}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the message to show quality selection
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"🎨 *Image Generation Setup*\n\n"
            f"*Prompt:* {prompt}\n"
            f"*Model:* {model}\n"
            f"*Size:* {size}\n\n"
            f"*Step 3: Select quality*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: str) -> None:
    """Show final confirmation with generate button."""
    session = user_sessions.get(session_id)
    if not session:
        return
    
    prompt = session["prompt"]
    model = session["model"]
    size = session["size"]
    quality = session["quality"]
    
    # Create final confirmation buttons
    keyboard = [
        [InlineKeyboardButton("🚀 Generate Image", callback_data=f"generate:{session_id}")],
        [
            InlineKeyboardButton("⬅️ Back", callback_data=f"back_quality:{session_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{session_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edit the message to show final confirmation
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"🎨 *Image Generation Setup - Final Confirmation*\n\n"
            f"*Prompt:* {prompt}\n"
            f"*Model:* {model}\n"
            f"*Size:* {size}\n"
            f"*Quality:* {quality}\n\n"
            f"Ready to generate your image!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data:
        return
    
    parts = data.split(":")
    action = parts[0]
    session_id = parts[1] if len(parts) > 1 else None
    
    if action == "model" and session_id:
        # Store selected model
        model = parts[2]
        user_sessions[session_id]["model"] = model
        user_sessions[session_id]["step"] = "size_selection"
        
        # Show size selection
        await show_size_selection(update, context, session_id)
        
    elif action == "size" and session_id:
        # Store selected size
        size = parts[2]
        user_sessions[session_id]["size"] = size
        user_sessions[session_id]["step"] = "quality_selection"
        
        # Show quality selection
        await show_quality_selection(update, context, session_id)
        
    elif action == "quality" and session_id:
        # Store selected quality
        quality = parts[2]
        user_sessions[session_id]["quality"] = quality
        user_sessions[session_id]["step"] = "confirmation"
        
        # Show final confirmation
        await show_final_confirmation(update, context, session_id)
        
    elif action == "generate" and session_id:
        # Generate the image
        await generate_image_from_session(update, context, session_id)
        
    elif action == "back_model" and session_id:
        # Go back to model selection
        user_sessions[session_id]["step"] = "model_selection"
        await show_model_selection(update, context, session_id)
        
    elif action == "back_size" and session_id:
        # Go back to size selection
        user_sessions[session_id]["step"] = "size_selection"
        await show_size_selection(update, context, session_id)
        
    elif action == "back_quality" and session_id:
        # Go back to quality selection
        user_sessions[session_id]["step"] = "quality_selection"
        await show_quality_selection(update, context, session_id)
        
    elif action == "cancel" and session_id:
        # Cancel and clean up
        if session_id in user_sessions:
            del user_sessions[session_id]
        
        await query.edit_message_text(
            "❌ Image generation cancelled.",
            reply_markup=None
        )

async def generate_image_from_session(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: str) -> None:
    """Generate image using the stored session parameters."""
    session = user_sessions.get(session_id)
    if not session:
        await update.callback_query.edit_message_text("❌ Session expired.")
        return
    
    query = update.callback_query
    prompt = session["prompt"]
    model = session["model"]
    size = session["size"]
    quality = session["quality"]
    
    # Show generating message
    status_message = await query.edit_message_text(
        f"🎨 *Generating Image...*\n\n"
        f"*Prompt:* {prompt}\n"
        f"*Model:* {model}\n"
        f"*Size:* {size}\n"
        f"*Quality:* {quality}\n\n"
        f"Please wait while we create your image...",
        parse_mode='Markdown'
    )
    
    try:
        # Generate the image
        result = image_service.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality
        )
        
        if result.is_successful() and result.data:
            # Send the generated image
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=result.data,
                caption=f"🎨 *Generated Image*\n\n"
                        f"*Prompt:* {prompt}\n"
                        f"*Model:* {result.model}\n"
                        f"*Size:* {result.size}\n"
                        f"*Quality:* {result.quality}",
                parse_mode='Markdown'
            )
            
            # Update the setup message to show completion
            await status_message.edit_text(
                f"✅ *Image Generated Successfully!*\n\n"
                f"*Prompt:* {prompt}\n"
                f"*Model:* {result.model}\n"
                f"*Size:* {result.size}\n"
                f"*Quality:* {result.quality}",
                parse_mode='Markdown'
            )
            
        else:
            error_msg = f"❌ Image generation failed: {result.error or 'Unknown error'}"
            await status_message.edit_text(error_msg)
            
            # If there's debug info, log it for troubleshooting
            if hasattr(result, 'debug_info') and result.debug_info:
                logger.debug(f"Image generation debug info: {result.debug_info}")
            elif hasattr(result, 'result') and result.result:
                logger.debug(f"Image generation raw result: {result.result}")
            
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        error_msg = f"❌ Error generating image: {str(e)}"
        await query.edit_message_text(error_msg)
    
    finally:
        # Clean up session
        if session_id in user_sessions:
            del user_sessions[session_id]

def register_handlers(application: Application) -> None:
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("img", handle_image_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query)) 