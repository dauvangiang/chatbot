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
from langchain_community.embeddings import SentenceTransformerEmbeddings
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
        if isinstance(doc, Document):
            doc = doc.page_content
        # resized_image = resize_base64_image(doc, size=(1280, 720))
        resized_image = resize_base64_image(doc, size=(1280, 1080))
        b64_images.append(resized_image)
    return {"images": b64_images}

def img_prompt_func(data_dict, num_images=2):
    messages = []
    ref_images = []
    try:
        print(f"Input to img_prompt_func: {data_dict}")  # Log toàn bộ dữ liệu đầu vào
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
                "Bạn là một chuyên gia phân tích, nhiệm vụ của bạn là trả lời các câu hỏi của người dùng. Những câu trả lời mà bạn đưa ra không nên chứa các từ khóa như: trong tài liệu, trong nội dung,...\n"
                "Nếu câu trả lời có nhiều ý, hãy chia các ý thành các gạch đầu dòng một cách rõ ràng.\n"
                "Bạn sẽ được cung cấp các nội dung liên quan (hoặc không) đến câu hỏi.\n"
                f"Bạn hãy sử dụng tất cả thông tin có sẵn, lịch sử trò chuyện và hiểu biết của bạn để trả lời câu hỏi của người dùng.\n"
                "Nếu bạn không thể tìm ra câu trả lời, hãy xin lỗi và thông báo cho người dùng biết.\n"
                "Câu hỏi của người dùng sẽ là một câu hỏi dạng văn bản hoặc câu hỏi trắc nghiệm và định dạng đầu ra mong đợi như sau:\n"
                '''
                ```response
                <Câu trả lời>.
                <Giải thích câu trả lời nếu có>.
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
    

@RunnableLambda
def parse_section(input_text):
        pattern = re.compile(rf'```response\n(.*?)```', re.DOTALL)
        text = pattern.findall(input_text)[0]
        return text 
    
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
    embedding_function=SentenceTransformerEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"),
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