# Paper Research Agent

一个面向论文阅读的 RAG Agent，支持文档导入、引用溯源和基于 DeepSeek 的论文问答。

## 当前状态

第一阶段：FastAPI 服务骨架。

## 远程开发启动

```bash
source /usr/local/anaconda/etc/profile.d/conda.sh
conda activate agent
cd /mnt/Data6/ys/paper-research-agent
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

首次使用时复制配置模板，并将 Key 填入项目根目录的 `.env` 文件：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```dotenv
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

`.env` 已被 Git 忽略，不会被提交。也可以继续使用系统环境变量，环境变量会覆盖 `.env` 中的同名配置。

模型和运行数据不会提交到 GitHub：

- `models/`：本地 BGE-M3 模型文件，首次运行前放置到 `models/bge-m3`，或通过
	`EMBEDDING_MODEL_PATH` 指定其他目录。
- `data/chroma_db/`：本地 Chroma 向量库，可通过重新导入论文生成。
- `data/papers/`：运行时上传的论文文件。

例如导入一篇论文：

```bash
python -m app.rag.ingest path/to/paper.pdf
```

模型文件较大，建议在服务器或本地单独下载，不要上传到 GitHub 仓库。

默认使用 DeepSeek 的 OpenAI 兼容接口和 `deepseek-chat` 模型，也可以通过以下环境变量覆盖：

```bash
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-chat"
```

远程服务器上运行后，在本地执行端口转发：

```bash
ssh -L 8000:localhost:8000 user@server
```

然后访问 <http://localhost:8000/docs>。
