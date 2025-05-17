from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from PIL import Image
from io import BytesIO
import base64
# from audio.speech_text import speech_to_text, text_to_speech_gtts  # Assuming these are in 'audio/speech_text.py'
from assets.other_context.orther import DICT  # Assuming this is in 'other_context/orther.py'
from rag_chroma_multi_modal.chain import chain, memory # Assuming this is where your chain and memory are defined
import re
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

memory.clear() # Clear memory when the API starts

def gen_response_logic(input_text: Optional[str] = None, audio_input_path: Optional[str] = None):
    try:
        # If an audio input is provided, transcribe it to text
        # if audio_input_path:
        #     input_text = speech_to_text(audio_input_path)

        if input_text:
            pattern = r'[^a-zA-Z0-9\sáàảãáạăằẳẵắặâầẩẫấậéèẻẽéẹêềểễếệíìỉĩíịóòỏõóọôồổỗốộơờởỡớợúùủũúụưừửữứựýỳỹỵỷđ]'
            tmp = re.sub(pattern, '', input_text.lower()).strip()
            if (tmp in DICT.keys()):
                # audio_output_path = text_to_speech_gtts(DICT.get(tmp))
                return DICT.get(tmp), None, None, None

            out_dict = chain.invoke(input_text)
            out_content = []
            out_content.append(out_dict["answer"])

            for bs64_img in out_dict["ref_images"]:
                image_data = base64.b64decode(bs64_img)
                img = Image.open(BytesIO(image_data))
                out_content.append(img)

            ref_images = out_dict["ref_images"]
            img_1_out = None
            img_2_out = None

            if len(ref_images) >= 1:
                image_data = base64.b64decode(ref_images[0])
                img_1_out = Image.open(BytesIO(image_data))
            if len(ref_images) >= 2:
                image_data = base64.b64decode(ref_images[1])
                img_2_out = Image.open(BytesIO(image_data))

            memory.save_context({"input": input_text}, {"output": out_dict["answer"]})

            out = out_dict["answer"]
            # out = out_dict["answer"].removeprefix("Trả lời: ")
            # audio_output_path = text_to_speech_gtts(out)
            audio_output_path = ""

            return out_content[0], audio_output_path, img_1_out, img_2_out
        else:
            return "Vui lòng nhập câu hỏi.", None, None, None
    except Exception as e:
        # print(e)
        # return "Đã có lỗi xảy ra. Vui lòng thử lại sau.", None, None, None
        print("Chain Error:", e)
        traceback.print_exc()
        return "Lỗi khi thực thi chuỗi RAG: " + str(e), None, None, None

app = FastAPI()

# Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các domain (hoặc có thể chỉ định một danh sách các domain cụ thể)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức HTTP (GET, POST, PUT, DELETE, ...)
    allow_headers=["*"],  # Cho phép tất cả các headers
)

class ChatRequest(BaseModel):
    text_input: Optional[str] = Form(None)
    audio_input_file: Optional[UploadFile] = None # Use Form and File for easier handling

class ChatResponse(BaseModel):
    answer: str
    audio_url: Optional[str] = None
    image_1_base64: Optional[str] = None
    image_2_base64: Optional[str] = None


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

@app.get("/favicon.ico")
async def get_favicon():
    """
    Trả về file favicon.ico.
    """
    favicon_path = "favicon.ico"  # Đặt đường dẫn đến file favicon.ico của bạn
    return FileResponse(favicon_path)

@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(
    text_input: Optional[str] = Form(None),
    audio_input_file: Optional[UploadFile] = File(None)
    # request: ChatRequest
):
    audio_path = None
    if audio_input_file:
        try:
            contents = await audio_input_file.read()
            # Save the uploaded audio file temporarily
            audio_path = f"temp_audio_{audio_input_file.filename}"
            with open(audio_path, 'wb') as f:
                f.write(contents)
        except Exception as e:
            print(f"Error processing audio upload: {e}")
            return JSONResponse(status_code=500, content={"message": "Failed to process audio"})

    answer, audio_output_path, img_1, img_2 = gen_response_logic(text_input, audio_path)

    image_1_base64 = None
    if img_1:
        buffered = BytesIO()
        img_1.save(buffered, format="PNG")  # You can change the format if needed
        image_1_base64 = base64.b64encode(buffered.getvalue()).decode()

    image_2_base64 = None
    if img_2:
        buffered = BytesIO()
        img_2.save(buffered, format="PNG")  # You can change the format if needed
        image_2_base64 = base64.b64encode(buffered.getvalue()).decode()

    return ChatResponse(
        answer=answer,
        audio_url=audio_output_path,
        image_1_base64=image_1_base64,
        image_2_base64=image_2_base64
    )


@app.get("/refresh_memory/")
async def refresh_memory():
    """
    Clears the chat memory.
    """
    memory.clear()
    return JSONResponse(status_code=200, content={"message": "Chat memory cleared"})

# To run this API, save it as a Python file (e.g., api.py) and run:
# uvicorn api:app --reload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)