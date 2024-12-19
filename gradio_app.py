import gradio as gr
from rag_chroma_multi_modal.chain import chain, memory
from PIL import Image
from io import BytesIO
import base64

def gen_response(input_text):
    try:
        out_dict = chain.invoke(input_text) # Wrap the text in a dictionary
        out_content = []
        out_content.append(out_dict["answer"])
        for bs64_img in out_dict["ref_images"]:
            image_data = base64.b64decode(bs64_img)
            img = Image.open(BytesIO(image_data))
            out_content.append(img)
        memory.save_context({"input": input_text}, {"output": out_dict["answer"]})
        return out_content
    except Exception as e:
        print(e)
        return "Something wrong happened. Please try again later.", "Something wrong happened. Please try again later.", "Something wrong happened. Please try again later."

input_text = gr.Textbox(label="Question", placeholder="Enter your question here", lines=2)

answer_output = gr.Textbox(label="Answer", interactive=False)
img_1 = gr.Image(label="Reference Image", interactive=False)
img_2 = gr.Image(label="Reference Image", interactive=False)
# img_3 = gr.Image(label="Reference Image", interactive=False)
    
# reset_button = gr.Button("Reset Memory")
# reset_button.click(reset_memory)

demo = gr.Interface(fn=gen_response, inputs=input_text, outputs=[answer_output, img_1, img_2])#, img_3])
demo.launch(share=True)