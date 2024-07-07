# Date    : 2024/7/4 22:18
# File    : app.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


# pip install -U langchain-huggingface

import os
import sys
import argparse
import logging
from loguru import logger
from typing import List, Optional, Union

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.concurrency import run_in_threadpool

import pydantic
from pydantic import BaseModel, Field

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

import torch
from transformers import AutoModel
from transformers import AutoTokenizer

from middleware_gzip import GZipRequestMiddleware
from jina import JinaTextEmbeddings
from bce import BCETextEmbeddings
from utils import logger


# 初始化argparse解析器
parser = argparse.ArgumentParser(description="text_embedder_app")
parser.add_argument('--model_name', type=str, default=None,
                    help="The name or path of the model to use. Default is None.")
parser.add_argument('--local_dir', type=str, default=None,
                    help="Directory to cache model files. Default is None.")
parser.add_argument('--device', type=str, default=None,
                    help="Device to use for model. Default is None.")
parser.add_argument('--normalize', type=bool, default=True,
                    help="Whether to normalize embeddings. Default is True.")
args = parser.parse_args()


E5_EMBED_INSTRUCTION = "passage: "
E5_QUERY_INSTRUCTION = "query: "
BGE_EN_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
BGE_ZH_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


router = APIRouter()


def create_app():
    initialize_embeddings()
    app = FastAPI(
        title="Text Embeddings API",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipRequestMiddleware)

    # handling gzip response only
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(router)

    return app


class CreateEmbeddingRequest(BaseModel):
    model: Optional[str] = Field(
        description="The model to use for generating embeddings.", default=None)
    input: Union[str, List[str]] = Field(description="The input to embed.")
    dimensions: Optional[int] = Field(
        description="The number of dimensions the resulting output embeddings should have.",
        default=None)
    user: Optional[str] = Field(default=None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "input": "The food was delicious and the waiter...",
                }
            ]
        }
    }


class Embedding(BaseModel):
    object: str
    embedding: List[float]
    index: int


class Usage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class CreateEmbeddingResponse(BaseModel):
    object: str
    data: List[Embedding]
    model: str
    usage: Usage


embeddings = None
tokenizer = None


def initialize_embeddings():
    global embeddings
    global tokenizer

    if args.device:
        device = args.device
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logger.info(f"Using device: {device}")

    if args.model_name is not None:
        model_name = args.model_name
        logger.info(f"Model name: {model_name}")
    else:
        raise ValueError("Model name cannot be None")

    model_dir = args.local_dir
    logger.info(f"Model local dir: {model_dir}")

    encode_kwargs = {
        "normalize_embeddings": args.normalize
    }
    logger.info(f"Need normalize embedding: {args.normalize}")

    if model_dir:
        tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    if "e5" in model_name:
        embeddings = HuggingFaceInstructEmbeddings(model_name=model_name,
                                                   embed_instruction=E5_EMBED_INSTRUCTION,
                                                   query_instruction=E5_QUERY_INSTRUCTION,
                                                   encode_kwargs=encode_kwargs,
                                                   model_kwargs={"device": device})
    elif "bge-" in model_name and "-en" in model_name:
        embeddings = HuggingFaceBgeEmbeddings(model_name=model_name,
                                              query_instruction=BGE_EN_QUERY_INSTRUCTION,
                                              encode_kwargs=encode_kwargs,
                                              model_kwargs={"device": device})
    elif "bge-" in model_name and "-zh" in model_name:
        embeddings = HuggingFaceBgeEmbeddings(model_name=model_name,
                                              query_instruction=BGE_ZH_QUERY_INSTRUCTION,
                                              encode_kwargs=encode_kwargs,
                                              model_kwargs={"device": device})
    elif "jina-" in model_name:
        embeddings = JinaTextEmbeddings(model_name=model_name,
                                        local_dir=model_dir,
                                        model_kwargs={
                                            "trust_remote_code": True,
                                            "torch_dtype": torch.bfloat16
                                        })
    elif "bce-" in model_name:
        model_name_or_path = model_name if not model_dir else model_dir
        embeddings = BCETextEmbeddings(model_name_or_path=model_name_or_path,
                                       pooler="cls",
                                       use_fp16=False,
                                       device=device,
                                       trust_remote_code=True)
    else:
        model_dir = model_name if not model_dir else model_dir
        embeddings = HuggingFaceEmbeddings(model_name=model_dir,
                                           encode_kwargs=encode_kwargs,
                                           model_kwargs={
                                               "device": device,
                                               "trust_remote_code": True
                                           })


def _create_embedding(input: Union[str, List[str]]):
    global embeddings
    
    model_name = args.model_name
    if model_name is None:
        raise ValueError("Model name cannot be None")

    # cutting HF model names like `jinaai/jina-embeddings-v2-base-zh`
    model_name_short = model_name.split("/")[-1]
    if isinstance(input, str):
        tokens = tokenizer.tokenize(input)
        return CreateEmbeddingResponse(data=[Embedding(embedding=embeddings.embed_query(input),
                                                       object="embedding", index=0)],
                                       model=model_name_short, object='list',
                                       usage=Usage(prompt_tokens=len(tokens), total_tokens=len(tokens)))
    else:
        data = [Embedding(embedding=embedding, object="embedding", index=i)
                for i, embedding in enumerate(embeddings.embed_documents(input))]
        total_tokens = 0
        for text in input:
            total_tokens += len(tokenizer.tokenize(text))
        return CreateEmbeddingResponse(data=data, model=model_name_short, object='list',
                                       usage=Usage(prompt_tokens=total_tokens, total_tokens=total_tokens))


@router.post(
    "/v1/embeddings",
    response_model=CreateEmbeddingResponse,
)
async def create_embedding(
        request: CreateEmbeddingRequest
):
    if pydantic.__version__ > '2.0.0':
        return await run_in_threadpool(
            _create_embedding, **request.model_dump(exclude={"user", "model", "model_config", "dimensions"})
        )
    else:
        return await run_in_threadpool(
            _create_embedding, **request.dict(exclude={"user", "model", "model_config", "dimensions"})
        )


if __name__ == "__main__":
    app = create_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=12308
    )
