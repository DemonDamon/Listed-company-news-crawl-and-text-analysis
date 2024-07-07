# embedding模型下载cli
- 参考：https://hf-mirror.com/
- 设置环境变量：$env:HF_ENDPOINT = "https://hf-mirror.com"
```bash
huggingface-cli download --resume-download jinaai/jina-embeddings-v2-base-zh --repo-type model --exclude "*.safetensors" "*.onnx" --local-dir ./jina-embeddings-v2-base-zh --local-dir-use-symlinks False

huggingface-cli download --resume-download sentence-transformers/all-MiniLM-L6-v2 --repo-type model --exclude "*.safetensors" "*.onnx" "*.ot" "*.h5" --local-dir ./all-MiniLM-L6-v2 --local-dir-use-symlinks False

huggingface-cli download --resume-download BAAI/bge-m3 --repo-type model --exclude "*.onnx" "*.onnx_data" --local-dir ./bge-m3 --local-dir-use-symlinks False

huggingface-cli download --resume-download maidalun1020/bce-embedding-base_v1 --repo-type model --local-dir ./bce-embedding-base_v1 --local-dir-use-symlinks False

huggingface-cli download --resume-download nomic-ai/nomic-embed-text-v1 --repo-type model --exclude "*.safetensors" "*.onnx" --local-dir ./nomic-embed-text-v1 --local-dir-use-symlinks False

```

# 开启服务
```bash
cd src/components/text_embedder

# 效果最差但是
python api_server.py --model_name sentence-transformers/all-MiniLM-L6-v2 --local_dir weights/all-MiniLM-L6-v2 --device cpu

python api_server.py --model_name jinaai/jina-embeddings-v2-base-zh --local_dir weights/jina-embeddings-v2-base-zh --device cpu

python api_server.py --model_name BAAI/bge-m3 --local_dir weights/bge-m3 --device cpu

python api_server.py --model_name maidalun1020/bce-embedding-base_v1 --local_dir weights/bce-embedding-base_v1 --device cpu

python api_server.py --model_name nomic-ai/nomic-embed-text-v1 --local_dir weights/nomic-embed-text-v1 --device cpu
```

# 测试脚本
```python
import requests
import json
import numpy as np

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
# print(response_json)

# 初始化embeddings列表
embeddings = []

# 遍历data数组
for item in response_json['data']:
    # 提取embedding字段的值并添加到列表中
    embeddings.append(np.array(item['embedding']))

cos_sim = lambda a, b: (a @ b.T) / (np.linalg.norm(a) * np.linalg.norm(b))

# 计算余弦相似度
print(cos_sim(embeddings[0], embeddings[1]))
```
- 简单测试结果

| 排名 | 模型 | 相似度 | 平均耗时（ms） | 设备 |
| ----- | ----- | ----- | ----- | ----- | 
| 1 | bge-m3 | **0.9607** | 130 | cpu |
| 2 | bce-embedding-base_v1 | 0.8771 | 60 | cpu |
| 3 | jina-embeddings-v2-base-zh | 0.7869 | 1500 | cpu |
| 4 | nomic-embed-text-v1 | 0.3414 | 60 | cpu |
| 4 | all-minilm-l6-v2 | 0.2106 | **30** | cpu |


# 参考
* https://hf-mirror.com/BAAI/bge-m3

# 模型参数
- 参考来源：https://huggingface.co/spaces/mteb/leaderboard

| 模型 | 参数大小（Million） | 显存占用（GB，FP32） | embedding维度 | 支持最大token数|
|----------|----------|----------|----------|----------|
| jina-embeddings-v2-base-zh | 161 |0.6 | 768 |8192 |
| bge-m3 | 568 | 2.12 | 1024 | 8194 |
| bge-large-zh-v1.5 | 326 | 1.21 | 1024 | 512 |
| bge-small-zh-v1.5 | 24 | 0.09 | 512 | 512 |
| m3e-base | 102 | 0.38 | 768 | 512 |
| m3e-large | 102  | 0.38  | 768 | 512 |
| text2vec-base-chinese | 102 | 0.38 | 768 | 512 |
| text2vec-large-chinese | 326 | 1.21 | 1024 | 512 |
| nomic-embed-text-v1 | 137 | 0.51 | 768 | 8192 |
| all-MiniLM-L6-v2 | 23 | 0.09 | 384 | 512 | 
| all-MiniLM-L12-v2 | 33 | 0.12 | 384 | 512 |
| bce-embedding-base_v1 | 279 | | | 512|

