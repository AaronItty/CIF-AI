import logging
import os
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from communication.sarvam_utils import get_sarvam_utils

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramBot:
    def __init__(self, token: str, agent_url: str):
        self.token = token
        self.agent_url = agent_url

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Extracts user message, forwards to Agent Core, and returns the response.
        """
        try:
            if not update.message or not update.message.text:
                return

            user_id = str(update.effective_user.id)
            session_id = str(update.effective_chat.id)
            message_text = update.message.text

            logging.info(f"Received text message from {user_id}: {message_text}")
            await self._process_and_respond(update, context, user_id, session_id, message_text)
        except Exception as e:
            logging.error(f"Error in handle_message: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ An internal error occurred.")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Downloads voice, translates via Sarvam, and forwards to Agent Core.
        """
        try:
            if not update.message or not update.message.voice:
                return

            user_id = str(update.effective_user.id)
            session_id = str(update.effective_chat.id)

            logging.info(f"Received voice message from {user_id}")

            # Download voice file
            voice_file = await update.message.voice.get_file()
            voice_path = f"voice_{session_id}_{update.message.message_id}.ogg"
            await voice_file.download_to_drive(voice_path)

            logging.info(f"Downloaded voice for {user_id} to {voice_path}, translating via Sarvam")

            # Translate via Sarvam (synchronous call - may block)
            sarvam = get_sarvam_utils()
            message_text = sarvam.speech_to_text_translate(voice_path).strip()

            # Cleanup
            if os.path.exists(voice_path):
                os.remove(voice_path)

            if not message_text:
                logging.warning(f"No transcription returned for voice from {user_id}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ Sorry, I couldn't understand the audio. Please try again or type your message."
                )
                return

            # Notify user of transcription
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎤 _Transcribed (ml -> en):_ {message_text}",
                parse_mode='Markdown'
            )

            logging.info(f"Transcribed voice from {user_id}: {message_text}")
            await self._process_and_respond(update, context, user_id, session_id, message_text, is_voice=True, is_malayalam=True)
        except Exception as e:
            logging.error(f"Error in handle_voice: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Error processing voice message.")

    async def _process_and_respond(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, session_id: str, message_text: str, is_voice: bool = False, is_malayalam: bool = False):
        # Prepare payload for Agent Core (NormalizedMessage schema)
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message_text,
            "channel": "telegram"
        }

        logging.info(f"Forwarding message from {user_id} to Agent Core")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.agent_url,
                    json=payload,
                    timeout=60.0  # Agent might take time to reason
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract agent's text response
                agent_response = data.get("response", "I'm sorry, I couldn't process that.")
                
                # Send text response (Always in English as requested)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=agent_response
                )

                # Synthesize and send voice response
                try:
                    sarvam = get_sarvam_utils()
                    voice_resp_path = f"resp_{session_id}_{update.message.message_id}.wav"
                    
                    tts_text = agent_response
                    tts_lang = "en-IN"
                    
                    if is_malayalam:
                        logging.info(f"Translating response to Malayalam for voice reply to {user_id}")
                        tts_text = sarvam.translate_text(agent_response, source_lang="en-IN", target_lang="ml-IN")
                        tts_lang = "ml-IN"
                        logging.info(f"Translated text: {tts_text[:50]}...")

                    sarvam.text_to_speech(tts_text, output_path=voice_resp_path, language_code=tts_lang)
                    
                    if os.path.exists(voice_resp_path):
                        with open(voice_resp_path, 'rb') as voice_audio:
                            await context.bot.send_voice(
                                chat_id=update.effective_chat.id,
                                voice=voice_audio
                            )
                        os.remove(voice_resp_path)
                except Exception as ve:
                    logging.error(f"Voice synthesis failed: {ve}")

        except Exception as e:
            logging.error(f"Error communicating with Agent Core: {e}")
            await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ Error: I'm having trouble connecting to my brain. Please try again later."
            )

    def run(self):
        """Starts the bot in polling mode."""
        application = ApplicationBuilder().token(self.token).build()
        
        message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)
        voice_handler = MessageHandler(filters.VOICE, self.handle_voice)
        
        application.add_handler(message_handler)
        application.add_handler(voice_handler)

        logging.info("Telegram bot started in polling mode with voice support...")
        application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    agent_url = os.getenv("AGENT_CORE_URL", "http://localhost:8002/api/v1/process_message")

    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment.")
    else:
        bot = TelegramBot(token, agent_url)
        bot.run()
