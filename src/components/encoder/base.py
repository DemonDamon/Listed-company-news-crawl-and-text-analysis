# Date    : 2024/7/7 5:33
# File    : base.py
# Desc    : 参考 https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/embeddings/embeddings.py
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


from abc import ABC, abstractmethod

from typing import (
    List,
    Optional,
    Union,
    Callable,
    TypeVar,
)
from typing_extensions import ParamSpec, TypedDict

import asyncio
from concurrent.futures import Executor, Future, ThreadPoolExecutor


# 定义一个参数规格（ParamSpec）名为 P，用于描述可变数量的位置参数和关键字参数的类型。
P = ParamSpec("P")

# 定义一个类型变量（TypeVar）名为 T，用于泛型类型，可以在函数、类或方法中代表任意类型的占位符。
T = TypeVar("T")


async def run_in_executor(
    executor: Optional[Executor],
    func: Callable[[P], T],
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """在执行器中运行一个函数。

    参数:
        executor (Executor): 要使用的执行器。
        func (Callable[[P], 输出]): 要运行的函数。
        *args (Any): 函数的位置参数。
        **kwargs (Any): 函数的关键字参数。

    返回:
        输出: 函数的执行结果。
    """

    def wrapper() -> T:
        try:
            return func(*args, **kwargs)
        except StopIteration as exc:
            # StopIteration 无法在 asyncio.Future 上设置，
            # 这会引发一个 TypeError 并且会让 Future 永远处于挂起状态，
            # 所以我们需要将它转换成一个 RuntimeError。
            raise RuntimeError from exc

    if executor_or_config is None or isinstance(executor_or_config, dict):
        # 使用从当前上下文中复制上下文的默认执行器
        return await asyncio.get_running_loop().run_in_executor(
            None,
            cast(Callable[..., T], partial(copy_context().run, wrapper)),
        )

    return await asyncio.get_running_loop().run_in_executor(executor_or_config, wrapper)


class Embeddings(ABC):
    """文本嵌入模型的接口。

    此接口旨在实现文本嵌入模型。

    文本嵌入模型用于将文本映射到向量（n维空间中的一个点）。

    相似的文本通常会被映射到该空间中彼此接近的点。具体而言，什么被认为是“相似”的以及在这个空间中如何衡量“距离”，这些细节依赖于特定的嵌入模型。

    这个抽象包含了用于嵌入文档列表的方法和用于嵌入查询文本的方法。查询文本的嵌入预期是一个单一的向量，而文档列表的嵌入预期是一系列的向量。

    通常情况下，查询嵌入与文档嵌入是相同的，但是这个抽象允许独立地处理它们。

    除了同步方法外，此接口还提供了这些方法的异步版本。

    默认情况下，异步方法是使用同步方法实现的；然而，为了性能原因，实现可以选择覆盖异步方法，使用原生异步实现。
    """

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """向量化检索文档"""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """向量化查询语句"""

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步向量化检索文档"""
        return await run_in_executor(None, self.embed_documents, texts)

    async def aembed_query(self, text: str) -> List[float]:
        """异步向量化查询语句"""
        return await run_in_executor(None, self.embed_query, text)
