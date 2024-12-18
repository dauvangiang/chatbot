from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import os
from pathlib import Path

import pypdfium2 as pdfium
from langchain_chroma import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings  # Add OpenCLIP
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


def get_images_from_pdf(pdf_path, img_dump_path):
    """
    Extract images from each page of a PDF document and save as JPEG files.

    :param pdf_path: A string representing the path to the PDF file.
    :param img_dump_path: A string representing the path to dummp images.
    """
    pdf = pdfium.PdfDocument(pdf_path)
    n_pages = len(pdf)
    for page_number in range(n_pages):
        page = pdf.get_page(page_number)
        bitmap = page.render(scale=1, rotation=0, crop=(0, 0, 0, 0))
        pil_image = bitmap.to_pil()
        pil_image.save(f"{img_dump_path}/img_{page_number + 1}.jpg", format="JPEG")


def get_images_from_pdf_2(pdf_dir, img_dump_path):
    """
    Extract images from each page of a PDF document and save as JPEG files.

    :param pdf_path: A string representing the path to the PDF file.
    :param img_dump_path: A string representing the path to dummp images.
    """
    pdf_files = os.listdir(pdf_dir)
    for pdf_file in pdf_files:
        pdf = pdfium.PdfDocument(pdf_dir + pdf_file)
        n_pages = len(pdf)
        for page_number in range(n_pages):
            page = pdf.get_page(page_number)
            bitmap = page.render(scale=1, rotation=0, crop=(0, 0, 0, 0))
            pil_image = bitmap.to_pil()
            pil_image.save(f"{img_dump_path}/{pdf_file[:-4]}_img_{page_number + 1}.jpg", format="JPEG")

# Load PDF
# doc_path = Path(__file__).parent / "docs/SIC_AI_Chapter1.pdf"
# img_dump_path = Path(__file__).parent / "docs/"

doc_path = "./slides/"
img_dump_path = "./images/"

# rel_doc_path = doc_path.relative_to(Path.cwd())
# rel_img_dump_path = img_dump_path.relative_to(Path.cwd())
pil_images = get_images_from_pdf_2(doc_path, img_dump_path)
vectorstore_text = Path(__file__).parent / "chroma_db_multi_modal_text"
re_vectorstore_text_path = vectorstore_text.relative_to(Path.cwd())

vectorstore_image = Path(__file__).parent / "chroma_db_multi_modal_image"
re_vectorstore_image_path = vectorstore_image.relative_to(Path.cwd())

# Load embedding function for text
text_embedding = SentenceTransformerEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# Load embedding function for images
image_embedding = OpenCLIPEmbeddings(model_name="ViT-L-14", checkpoint="openai")  # Use OpenCLIP for images

# Create chroma
vectorstore_text_mmembd = Chroma(
    collection_name="multi-modal-rag-text",
    persist_directory=str(Path(__file__).parent / "chroma_db_multi_modal_text"),
    embedding_function=text_embedding # Only use text_embedding for text
)

# Create chroma vector store for images
vectorstore_image_mmembd = Chroma(
    collection_name="multi-modal-rag-image",
    persist_directory=str(Path(__file__).parent / "chroma_db_multi_modal_image"),
    embedding_function=image_embedding
)

# Get image URIs
image_uris = sorted(
    [
        os.path.join(img_dump_path, image_name)
        for image_name in os.listdir(img_dump_path)
        if image_name.endswith(".jpg")
    ]
)
   
# Get text from pdf
docs = []
pdf_files = os.listdir(doc_path)
for pdf_file in pdf_files:
    loader = PyPDFLoader(doc_path+pdf_file)
    loaded_docs = loader.load()
    print(f"Loaded documents for {pdf_file}: {len(loaded_docs)}")
    docs.extend(loaded_docs)

print("========Docs========")
for doc in docs:
    print(doc.page_content[:100])

text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=100)
splits = text_splitter.split_documents(docs)
print(f"Number of text splits: {len(splits)}")

# Add text
vectorstore_text_mmembd.add_documents(documents=splits)

# Add images with image embedding
vectorstore_image_mmembd.add_images(uris=image_uris, embedding=image_embedding) # Use OpenCLIP embedding here