from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from rag_chroma_multi_modal.chain import chain
from langchain_core.runnables import RunnableLambda
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

add_routes(app, chain)

@app.post("/gen_answer")
async def gen_answer(text: str):
    try:
        return chain.invoke(text)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to generate answer. Please try again later!")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)