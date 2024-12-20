import whisper
import pyttsx3
import tempfile
from pydub import AudioSegment
from gtts import gTTS
import torch

# Initialize Whisper model (You can move it outside function to save time if use gradio as a service)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=DEVICE)

# Initialize pyttsx3 engine
bot = pyttsx3.init()
bot.setProperty('rate', 150)

def speech_to_text(audio_file):
  """Transcribe audio to text using Whisper."""
  try:
    audio = whisper.load_audio(audio_file)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    
    # Prepare decoding options
    options = whisper.DecodingOptions(language="vi", fp16=True)
    
    # Decode the audio
    result = whisper.decode(model, mel, options)
    
    # Return text
    return result.text
  except Exception as e:
      print(e)
      return None
    
def text_to_speech(text):
    """Converts text to speech and returns the audio file path (as MP3)."""
    try:
        wav_file_path = "./audio/output.wav"  # Thay đổi đường dẫn nếu cần
        bot.save_to_file(text, wav_file_path)
        bot.runAndWait()

        mp3_fp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        audio = AudioSegment.from_wav(wav_file_path)
        audio.export(mp3_fp.name, format="mp3")
        return mp3_fp.name
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")
        return None
    
def text_to_speech_gtts(text, lang='vi', speed=1.27):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            tts.save(fp.name)
            # return fp.name

            audio = AudioSegment.from_mp3(fp.name)
            # Tăng tốc độ bằng cách thay đổi frame_rate
            faster_audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            })
            faster_audio = faster_audio.set_frame_rate(audio.frame_rate) # Cập nhật lại frame_rate

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_faster_speed_file:
                faster_audio.export(tmp_faster_speed_file.name, format="mp3")
                return tmp_faster_speed_file.name
    except Exception as e:
        print(f"Error during gTTS conversion: {e}")
        return None