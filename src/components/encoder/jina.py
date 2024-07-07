# Date    : 2024/7/5 10:41
# File    : jina_embedding.py
# Desc    : 参考 https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/embeddings/huggingface.py
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import os
import sys
from typing import (
    Any,
    Dict,
    List,
    Optional
)

from loguru import logger
import sentence_transformers
from pydantic.v1 import BaseModel, Extra, Field

from base import Embeddings


class JinaTextEmbeddings(BaseModel, Embeddings):
    """Jina embedding models."""

    client: Any  #: :meta private:
    model_name: str = "jina-embeddings-v2-base-zh"
    """Model name to use."""
    local_dir: Optional[str] = None
    """Path to store models. 
    Can be also set by SENTENCE_TRANSFORMERS_HOME environment variable."""
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """Keyword arguments to pass to the Sentence Transformer model, such as `device`,
    `prompts`, `default_prompt_name`, `revision`, `trust_remote_code`, or `token`.
    See also the Sentence Transformer documentation: https://sbert.net/docs/package_reference/SentenceTransformer.html#sentence_transformers.SentenceTransformer"""
    encode_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """Keyword arguments to pass when calling the `encode` method of the Sentence
    Transformer model, such as `prompt_name`, `prompt`, `batch_size`, `precision`,
    `normalize_embeddings`, and more.
    See also the Sentence Transformer documentation: https://sbert.net/docs/package_reference/SentenceTransformer.html#sentence_transformers.SentenceTransformer.encode"""
    multi_process: bool = False
    """Run encode() on multiple GPUs."""
    show_progress: bool = False
    """Whether to show a progress bar."""

    def __init__(self, **kwargs: Any):
        """Initialize the sentence_transformer."""
        super().__init__(**kwargs)
        try:
            from transformers import AutoModel

        except ImportError as exc:
            raise ImportError(
                "Could not import `AutoModel` from transformers"
                "Please install it with `pip install -U transformers`."
            ) from exc

        device = self.model_kwargs.get("device", "cpu")
        if self.local_dir:
            self.client = AutoModel.from_pretrained(
                self.local_dir, **self.model_kwargs
            )
            self.client.to(device)
        else:
            self.client = AutoModel.from_pretrained(
                self.model_name, **self.model_kwargs
            )
            self.client.to(device)
        logger.info(f"model load successfully")

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a HuggingFace transformer model.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        texts = list(map(lambda x: x.replace("\n", " "), texts))
        if self.multi_process:
            if isinstance(self.client, sentence_transformers.SentenceTransformer):
                pool = self.client.start_multi_process_pool()
                embeddings = self.client.encode_multi_process(texts, pool)
                sentence_transformers.SentenceTransformer.stop_multi_process_pool(pool)
            else:
                raise ValueError("multi_process is only supported for SentenceTransformer")
        else:
            embeddings = self.client.encode(
                texts, show_progress_bar=self.show_progress, **self.encode_kwargs
            )
            logger.info(f"text encoding successfully")

        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        return self.embed_documents([text])[0]
