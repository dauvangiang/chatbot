import gradio as gr
from rag_chroma_multi_modal.chain import chain, memory
from PIL import Image
from io import BytesIO
import base64
from audio.speech_text import *

memory.clear()

def gen_response(input_text, audio_input):
    try:
        # If an audio input is provided, transcribe it to text
        if audio_input:
            input_text = speech_to_text(audio_input)
            print("Transcribe success! Text:", input_text)

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
        
        # Convert the answer to speech
        audio_output = text_to_speech(out_dict["answer"])
        # audio_output = text_to_speech("Hello")
        print(audio_output)
        
        return out_content[0], img_1_out, img_2_out, audio_output
    except Exception as e:
        print(e)
        return "Something wrong happened. Please try again later.", None, None, None

input_text = gr.Textbox(label="Question", placeholder="Enter your question here", lines=2)

answer_output = gr.Textbox(label="Answer", interactive=False)
img_1 = gr.Image(label="Reference Image", interactive=False)
img_2 = gr.Image(label="Reference Image", interactive=False)
# img_3 = gr.Image(label="Reference Image", interactive=False)

audio_input = gr.Audio(type="filepath", label="Voice input", sources=["microphone"])
audio_output = gr.Audio(label="Voice output")
    
# reset_button = gr.Button("Reset Memory")
# reset_button.click(reset_memory)

demo = gr.Interface(fn=gen_response, inputs=[input_text, audio_input], outputs=[answer_output, img_1, img_2, audio_output])#, img_3])
demo.launch(share=True)