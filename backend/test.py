from langchain_experimental.open_clip import OpenCLIPEmbeddings

emb = OpenCLIPEmbeddings(model_name="ViT-L-14", checkpoint="openai")
print(emb.embed_query("Hello world"))
