import os
import logging
from sarvamai import SarvamAI
from sarvamai.play import save

logger = logging.getLogger(__name__)

class SarvamUtils:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY")
        if not self.api_key:
            logger.error("SARVAM_API_KEY not found in environment.")
            raise ValueError("SARVAM_API_KEY is required.")
        self.client = SarvamAI(api_subscription_key=self.api_key)

    def speech_to_text_translate(self, audio_file_path: str) -> str:
        """
        Transcribes/Translates Malayalam audio into English text.
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.speech_to_text.transcribe(
                    file=audio_file,
                    model="saaras:v3",
                    mode="translate"  # Directly translates Malayalam to English
                )
            
            # The Sarvam SDK returns a SpeechToTextResponse object, not a dict
            if hasattr(response, 'transcript'):
                return response.transcript
            elif isinstance(response, dict):
                return response.get('transcript', "")
            return str(response)
        except Exception as e:
            logger.error(f"Error in Sarvam STT: {e}")
            return ""

    def translate_text(self, text: str, source_lang: str = "en-IN", target_lang: str = "ml-IN") -> str:
        """
        Translates text between languages using Mayura:v1.
        """
        try:
            # The Mayura model has a 1000 char limit
            if len(text) > 1000:
                text = text[:997] + "..."
            
            response = self.client.text.translate(
                input=text,
                model="mayura:v1",
                source_language_code=source_lang,
                target_language_code=target_lang
            )
            
            if hasattr(response, 'translated_text'):
                return response.translated_text
            elif isinstance(response, dict):
                return response.get('translated_text', "")
            return str(response)
        except Exception as e:
            logger.error(f"Error in Sarvam Translate: {e}")
            return text  # Return original if translation fails

    def text_to_speech(self, text: str, output_path: str = "response_output.wav", language_code: str = "en-IN") -> str:
        """
        Converts text back into speech.
        """
        try:
            # Options for target_language_code: 'hi-IN', 'ml-IN', 'en-IN'
            audio = self.client.text_to_speech.convert(
                target_language_code=language_code,
                text=text,
                model="bulbul:v3",
                speaker="shubh" # Options: shubh, arpit, etc.
            )
            save(audio, output_path)
            return output_path
        except Exception as e:
            logger.error(f"Error in Sarvam TTS: {e}")
            return ""

# Singleton instance
_sarvam_utils = None

def get_sarvam_utils() -> SarvamUtils:
    global _sarvam_utils
    if _sarvam_utils is None:
        _sarvam_utils = SarvamUtils()
    return _sarvam_utils
