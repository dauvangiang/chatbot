from dotenv import find_dotenv, load_dotenv
import os

# load_dotenv(find_dotenv(usecwd=True))
load_dotenv()


import base64
import io
from pathlib import Path
import re
from operator import itemgetter

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic.v1 import BaseModel
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableSequence
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from PIL import Image
# from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory

api_key = os.getenv("GOOGLE_API_KEY")

def resize_base64_image(base64_string, size=(128, 128)):
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data))
    resized_img = img.resize(size, Image.LANCZOS)
    buffered = io.BytesIO()
    resized_img.save(buffered, format=img.format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def get_resized_images(docs):
    b64_images = []
    for doc in docs:
        try:
            if isinstance(doc, Document):
                doc = doc.page_content
            resized_image = resize_base64_image(doc, size=(1280, 1080))
            b64_images.append(resized_image)
        except Exception as e:
            print(f"[Image Resize Error]: {e}")
    return {"images": b64_images}

def img_prompt_func(data_dict, num_images=2):
    messages = []
    ref_images = []
    try:
        # print(f"Input to img_prompt_func: {data_dict}")  # Log toàn bộ dữ liệu đầu vào
        if data_dict["context"]["images"]:
            for image in data_dict["context"]["images"]["images"]:
                image_message = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image}"},
                }
                messages.append(image_message)
                ref_images.append(image)

        # print(f"Generated ref_images: {ref_images}")  # Log giá trị ref_images

        # Add chat history to the prompt
        chat_history = data_dict.get("chat_history", [])
        for message in chat_history:
            if isinstance(message, HumanMessage):
               messages.append({"type": "text", "text": f"User: {message.content}"})
            elif isinstance(message, AIMessage):
                messages.append({"type": "text", "text": f"Assistant: {message.content}"})

        text_message = {
            "type": "text",
            "text": (
                "Bạn là một trợ lý AI thông minh, bạn hãy trả lời các câu hỏi của người dùng liên quan đến các thông tin về Trường Đại học Thủy lợi. Câu trả lời mà bạn đưa ra không nên chứa các từ khóa ngữ cảnh như: Trong tài liệu, trong văn bản,...\n"
                "Bạn hãy định dạng câu trả lời thành nội dung có các thẻ HTML một cách phù hợp, ví dụ như xuống dòng (<br>), in đậm (<b></b>), liệt kê (<ul></ul>, <li></li>),... và nhiều cách định dạng bằng thẻ HTML phù hợp khác."
                "Bạn sẽ được cung cấp các nội dung có thể có liên quan đến câu hỏi, bạn cũng có thể sử dụng các thông tin mà bạn biết hoặc các thông tin trên Internet về Trường Đại học Thủy lợi.\n"
                f"Bạn hãy trả lời câu hỏi của người dùng bằng những gì mà bạn biết.\n"
                "Nếu bạn không thể tìm ra câu trả lời, hãy xin lỗi và thông báo cho người dùng biết. Đồng thời, gợi ý cho người dùng tìm hiểu ở các nguồn khác nhau như Google, fanpage chính thức, Zalo OA, cố vấn học tập, hoặc các kênh thông tin chính thức khác của Trường Đại học Thủy lợi. Chú ý định dạng câu trả lời sử dụng các thẻ HTML hợp lý.\n"
                "Câu hỏi của người dùng sẽ là một câu hỏi dạng văn bản hoặc câu hỏi trắc nghiệm và định dạng đầu ra mong đợi như sau:\n"
                '''
                ```
                <Câu trả lời>.
                <Giải thích câu trả lời (nếu có)>.
                ```
                '''
                f"Câu hỏi của người dùng: {data_dict['question']}\n\n"
            ),
        }
        messages.append(text_message)
        out = [HumanMessage(content=messages)]
        # print(f"Generated prompt: {out}")
        return {'prompt': out, 'ref_images': ref_images}
    except Exception as e:
        print(f"Error in img_prompt_func: {e}")
        return {'prompt': [], 'ref_images': []}
    

# @RunnableLambda
# def parse_section(input_text):
#         pattern = re.compile(rf'```response\n(.*?)```', re.DOTALL)
#         text = pattern.findall(input_text)[0]
#         return text

@RunnableLambda
def parse_section(input_text):
    """
    Trích xuất nội dung từ thẻ ```response``` và bọc nội dung trong các thẻ HTML.
    """
    try:
        # Sử dụng regex để trích xuất nội dung giữa các thẻ ```response```
        pattern = re.compile(rf'```html(.*?)```', re.DOTALL)
        matches = pattern.findall(input_text)

        if not matches:
            return input_text
        
        return matches[0].strip()

        # Thêm các thẻ HTML phù hợp
        # html_response = f"<div class='response'><p>{text.replace('\n', '<br/>')}</p></div>"
        # return html_response
        return text
    except IndexError:
        print("Error: No response block found in the input text.")
        # return "<div class='response'><p>Error: No response found.</p></div>"
        return input_text
    
@RunnableLambda
def answer_text2dict(text):
    lines = text.strip().splitlines()
    parsed_dict = {}
    for line in lines:
        key, value = line.split(":", 1)
        parsed_dict[key.strip()] = value.strip()
    return parsed_dict


def multi_modal_rag_chain(retriever_text, retriever_image, memory):
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=1.0, convert_to_markdown=False, api_key=api_key)

    chain = (
        {
           "context": {
               "images": retriever_image | RunnableLambda(get_resized_images),
               "texts": retriever_text,
           },
            "question": RunnablePassthrough(),
            "chat_history": RunnableLambda(lambda x: memory.load_memory_variables(inputs=x)['history']),
        }
        | RunnableLambda(img_prompt_func)
        | {
            'answer': itemgetter('prompt') | model 
              | RunnableLambda(lambda model_output: log_and_return(model_output, "Model Output")) 
              | StrOutputParser() 
              | RunnableLambda(lambda parsed_output: log_and_return(parsed_output, "Parsed Output")) 
              | parse_section,
            'ref_images': itemgetter('ref_images')
        }
    )

    return chain

def log_and_return(data, label):
    print(f"{label}: {data}")
    return data


# Load chroma text
vectorstore_text_mmembd = Chroma(
    collection_name="multi-modal-rag-text",
    persist_directory=str(Path(__file__).parent.parent / "chroma_db_multi_modal_text"),
    # embedding_function=SentenceTransformerEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"),
    embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"),
)

# Make retriever
retriever_text_mmembd = vectorstore_text_mmembd.as_retriever()

# Load chroma image
vectorstore_image_mmembd = Chroma(
    collection_name="multi-modal-rag-image",
     persist_directory=str(Path(__file__).parent.parent / "chroma_db_multi_modal_image"),
     embedding_function=OpenCLIPEmbeddings(
         model_name="ViT-L-14", checkpoint="openai"
     ),
 )
 
# Make retriever image
retriever_image_mmembd = vectorstore_image_mmembd.as_retriever()

# Initialize memory
memory = ConversationBufferMemory(return_messages=True)


# Create RAG chain
chain = multi_modal_rag_chain(retriever_text_mmembd, retriever_image_mmembd, memory)


class Question(BaseModel):
    __root__: str


chain = chain.with_types(input_type=Question)