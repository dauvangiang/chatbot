import gradio as gr
from rag_chroma_multi_modal.chain import chain
from PIL import Image
from io import BytesIO
import base64

def gen_response(input_text):
    try:
        out_dict = chain.invoke(input_text)
        out_content = []
        out_content.append(out_dict["answer"])
        for bs64_img in out_dict["ref_images"]:
            image_data = base64.b64decode(bs64_img)
            img = Image.open(BytesIO(image_data))
            out_content.append(img)
        return out_content
        # out_dict = chain.invoke(input_text)
        # return out_dict["answer"], out_dict["explanation"]
    except Exception as e:
        return "Something wrong happened. Please try again later.", "Something wrong happened. Please try again later.", "Something wrong happened. Please try again later."

# with gr.Blocks() as demo:
input_text = gr.Textbox(label="Question", placeholder="Enter your question here", lines=2)

answer_output = gr.Textbox(label="Answer", interactive=False)
img_1 = gr.Image(label="Reference Image", interactive=False)
img_2 = gr.Image(label="Reference Image", interactive=False)
# img_3 = gr.Image(label="Reference Image", interactive=False)
# explaination_output = gr.Textbox(label="Explanation", interactive=False)
    
#     ask_button = gr.Button(value="Ask")
    
#     ask_button.click(gen_response, inputs = [input_text], outputs = [answer_output, explaination_output])

# demo.launch()

# demo = gr.Interface(fn=gen_response, inputs=input_text, outputs=[answer_output, explaination_output])
demo = gr.Interface(fn=gen_response, inputs=input_text, outputs=[answer_output, img_1, img_2])#, img_3])
demo.launch(share=True)