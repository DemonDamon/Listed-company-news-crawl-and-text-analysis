# Date    : 2024/7/4 22:33
# File    : test_jina_embedding_v2.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


# !pip install transformers
import os
import torch
from transformers import AutoModel
import numpy as np


cos_sim = lambda a, b: (a @ b.T) / (np.linalg.norm(a) * np.linalg.norm(b))


def test_jina():
    if os.path.exists('../weights/jina-embeddings-v2-base-zh'):
        model_name_or_path = '../weights/jina-embeddings-v2-base-zh'
    else:
        model_name_or_path = 'jaai/jina-embeddings-v2-base-zh'

    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

    model_1 = AutoModel.from_pretrained(model_name_or_path,
                                        trust_remote_code=True,
                                        torch_dtype=torch.bfloat16)
    import time
    st = time.time()
    embeddings = model_1.encode(['How is the weather today?', '今天天气怎么样?'])
    # 0.7868529
    print(cos_sim(embeddings[0], embeddings[1]))
    et = time.time()
    print(et - st)


def test_api_service():
    import requests
    import json

    url = "http://127.0.0.1:12308/v1/embeddings"

    payload = json.dumps({
        "input": [
            "How is the weather today?",
            "今天天气怎么样?"
        ]
    })
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # 解析JSON字符串
    response_json = json.loads(response.text)

    # 初始化embeddings列表
    embeddings = []

    # 遍历data数组
    for item in response_json['data']:
        # 提取embedding字段的值并添加到列表中
        embeddings.append(np.array(item['embedding']))

    # 打印结果
    print(cos_sim(embeddings[0], embeddings[1]))


if __name__ == "__main__":
    # test_inference()
    test_api_service()
