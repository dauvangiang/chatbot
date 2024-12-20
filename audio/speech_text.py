import whisper
import pyttsx3
from io import BytesIO
import tempfile
import os
from pydub import AudioSegment
import time

# Initialize Whisper model (You can move it outside function to save time if use gradio as a service)
model = whisper.load_model("base")

# Initialize pyttsx3 engine
bot = pyttsx3.init()
bot.setProperty('rate', 150)

def speech_to_text(audio_file):
    """Transcribe audio to text using Whisper."""
    try:
        
        # Load audio file from file path
        audio = whisper.load_audio(audio_file)

        # Pad or trim audio to 30 seconds (for whisper)
        audio = whisper.pad_or_trim(audio)

        # Get Log-Mel spectrogram (for whisper)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        
        # Detect language
        _, probs = model.detect_language(mel)
        
        # Prepare decoding options
        options = whisper.DecodingOptions()
        
        # Decode the audio
        result = whisper.decode(mel, options)
        
        # Return text
        return result.text
    except Exception as e:
        print(e)
        return None
    
def text_to_speech(text):
    """Convert text to speech using pyttsx3 and return MP3 file content."""
    if not text:
        return None
    wav_tmp_file = None
    mp3_tmp_file = None
    try:
      # Create a temporary WAV file
       with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_tmp_file:
            print(f"Created WAV temp file: {wav_tmp_file.name}")
            bot.save_to_file(text, wav_tmp_file.name)
            print(f"Saved to WAV file: {wav_tmp_file.name}")
            bot.runAndWait()
            print("RunAndWait success")
       
            # Convert WAV to MP3
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_tmp_file:
              print(f"Created MP3 temp file: {mp3_tmp_file.name}")
              audio = AudioSegment.from_wav(wav_tmp_file.name)
              audio.export(mp3_tmp_file.name, format="mp3")
              print(f"Convert from WAV to MP3 successfully! at {mp3_tmp_file.name}")

              with open(mp3_tmp_file.name, "rb") as mp3_file:
                 audio_bytes = mp3_file.read()
                 print(f"Read MP3 bytes successfully!")
              
              
              return audio_bytes
    except Exception as e:
      print(f"Error: {e}")
      return None
    finally:
       if wav_tmp_file:
         print(f"Removing file: {wav_tmp_file.name}")
         os.remove(wav_tmp_file.name) #remove file if exists.
       if mp3_tmp_file:
         print(f"Removing file: {mp3_tmp_file.name}")
         os.remove(mp3_tmp_file.name)