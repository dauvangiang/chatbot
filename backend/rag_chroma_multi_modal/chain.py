from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

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
    if data_dict["context"]["images"]:
        for image in data_dict["context"]["images"]["images"]:
            image_message = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            }
            messages.append(image_message)
            ref_images.append(image)

    # Add chat history to the prompt
    chat_history = data_dict.get("chat_history", [])
    for message in chat_history:
        if isinstance(message, HumanMessage):
           messages.append({"type": "text", "text": f"User: {message.content}"})
        elif isinstance(message, AIMessage):
            messages.append({"type": "text", "text": f"Assistant: {message.content}"})

    # text_message = {
    #     "type": "text",
    #     "text": (
    #         "Bạn là một chuyên gia phân tích, nhiệm vụ của bạn là trả lời các câu hỏi về nội dung trực quan.\n"
    #         "Bạn sẽ được cung cấp một hoặc nhiều hình ảnh từ một bộ slide trình bày.\n"
    #         f"Bạn có thể có thêm thông tin từ văn bản của bộ slide đó. Hãy sử dụng tất cả thông tin có sẵn và lịch sử trò chuyện để trả lời câu hỏi của người dùng.\n"
    #         "Câu hỏi của người dùng sẽ là một câu hỏi dạng văn bản hoặc câu hỏi trắc nghiệm và định dạng đầu ra mong đợi như sau:\n"
    #         '''
    #         ```response
    #         Trả lời: <câu trả lời đúng>
    #         Giải thích: <giải thích tại sao đáp án đó đúng>
    #         ```
    #         '''
    #         f"Câu hỏi của người dùng: {data_dict['question']}\n\n"
    #     ),
    # }
    text_message = {
        "type": "text",
        "text": (
            "Bạn là một chuyên gia phân tích, nhiệm vụ của bạn là trả lời các câu hỏi của người dùng.\n"
            "Bạn sẽ được cung cấp một hoặc nhiều hình ảnh từ một bộ slide trình bày.\n"
            f"Bạn có thể có thêm thông tin từ văn bản của bộ slide đó. Hãy sử dụng tất cả thông tin có sẵn và lịch sử trò chuyện để trả lời câu hỏi của người dùng.\n"
            "Nếu không tìm thấy thông tin từ tài liệu được cung cấp, bạn hãy sử dụng sự hiểu biết của mình để trả lời câu hỏi. Và hãy trả lời một cách chính xác nhất.\n"
            "Nếu bạn vẫn không thể tìm ra câu trả lời, hãy thông báo cho người dùng biết rằng không có thông tin liên quan mà người dùng cần tìm.\n"
            "Câu hỏi của người dùng sẽ là một câu hỏi dạng văn bản hoặc câu hỏi trắc nghiệm và định dạng đầu ra mong đợi như sau:\n"
            '''
            ```response
            <Câu trả lời đúng>.
            <Giải thích tại sao đáp án đó đúng>
            ```
            '''
            f"Câu hỏi của người dùng: {data_dict['question']}\n\n"
        ),
    }
    messages.append(text_message)
    out = [HumanMessage(content=messages)]
    return {'prompt': out, 'ref_images': ref_images}
    

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
    # model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0, convert_to_markdown=False)
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.0, convert_to_markdown=False)

    # Define the RAG pipeline
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
        | {'answer': itemgetter('prompt') | model | StrOutputParser() | parse_section, 
         'ref_images': itemgetter('ref_images')}
    )

    return chain


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