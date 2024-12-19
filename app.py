from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from rag_chroma_multi_modal.chain import chain, memory
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

@app.on_event("startup")
async def startup_event():
    memory.clear()

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

add_routes(app, chain)

@app.post("/gen_answer")
async def gen_answer(text: str):
    try:
        response = chain.invoke(text)
        memory.save_context({"input": text}, {"output": response["answer"]})
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate answer. Please try again later! Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)