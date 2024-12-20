import gradio as gr
from rag_chroma_multi_modal.chain import chain, memory
from PIL import Image
from io import BytesIO
import base64
from audio.speech_text import *
from other_context.orther import DICT
import re

memory.clear()

def gen_response(input_text, audio_input):
    try:
        # If an audio input is provided, transcribe it to text
        if audio_input:
            input_text = speech_to_text(audio_input)

        pattern = r'[^a-zA-Z0-9\sáàảãáạăằẳẵắặâầẩẫấậéèẻẽéẹêềểễếệíìỉĩíịóòỏõóọôồổỗốộơờởỡớợúùủũúụưừửữứựýỳỹỵỷđ]'
        tmp = re.sub(pattern, '', input_text.lower()).strip()
        if (tmp in DICT.keys()):
            audio_output_path = text_to_speech_gtts(DICT.get(tmp))
            return DICT.get(tmp), audio_output_path, None, None

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
       
        out = out_dict["answer"].removeprefix("Trả lời: ")
        audio_output_path = text_to_speech_gtts(out)
        
        return out_content[0], audio_output_path, img_1_out, img_2_out
        # return out_content[0], img_1_out, img_2_out, audio_output
    except Exception as e:
        print(e)
        return "Đã có lỗi xảy ra. Vui lòng thử lại sau.", None, None, None

input_text = gr.Textbox(label="Câu hỏi:", placeholder="Nhập câu hỏi ở đây hoặc sử dụng voice chat ở bên dưới...", lines=2)

answer_output = gr.Textbox(label="Câu trả lời:", interactive=False)
img_1 = gr.Image(label="Ảnh minh họa", interactive=False)
img_2 = gr.Image(label="Ảnh minh họa", interactive=False)
# img_3 = gr.Image(label="Reference Image", interactive=False)

audio_input = gr.Audio(type="filepath", label="Voice chat", sources=["microphone"])
audio_output = gr.Audio(label="Voice")

demo = gr.Interface(fn=gen_response, inputs=[input_text, audio_input], outputs=[answer_output, audio_output, img_1, img_2])#, img_3])
demo.launch(share=True)