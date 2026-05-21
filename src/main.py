"""
CAAC-RegSearch Windows 打包入口
"""
import sys
import os
import json
import pkgutil
import tempfile
import shutil
import re

# 打包后，将 data 目录内容解压到程序目录
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(APP_DIR, "data")
INDEX_FILE = os.path.join(DATA_DIR, "docs.json")

# ===================== 分词 & BM25 检索 =====================
import jieba
from rank_bm25 import BM25Okapi

jieba.setLogLevel(jieba.logging.INFO)

_tokenizer_cache = None
_bm25_cache = None
_docs_cache = None


def tokenize(text: str):
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s]", " ", text)
    return [w.strip() for w in jieba.cut(text) if w.strip() and len(w.strip()) > 1]


def load_index():
    global _bm25_cache, _docs_cache
    if _bm25_cache is None:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _docs_cache = data["docs"]
        tokenized = data["tokenized"]
        _bm25_cache = BM25Okapi(tokenized)
    return _bm25_cache, _docs_cache


def search(query: str, top_k: int = 5):
    if not query or not query.strip():
        return []
    try:
        bm25, docs = load_index()
    except Exception:
        return []
    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)
    ranked = sorted(zip(scores, docs), key=lambda x: -x[0])
    results = []
    for score, doc in ranked[:top_k]:
        if score <= 0:
            continue
        snippet = _extract_snippet(doc["content"], query_tokens)
        results.append({
            "title": doc["title"],
            "content": snippet,
            "source_file": doc["source"],
            "score": round(float(score), 4),
        })
    return results


def _extract_snippet(content: str, query_tokens, window=120):
    content_lower = content.lower()
    first_pos = -1
    for token in query_tokens:
        pos = content_lower.find(token.lower())
        if pos != -1 and (first_pos == -1 or pos < first_pos):
            first_pos = pos
    if first_pos == -1:
        return content[:200].strip()
    start = max(0, first_pos - window)
    end = min(len(content), first_pos + window)
    snippet = content[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet


# ===================== FastAPI 应用 =====================
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="CAAC-RegSearch", description="民航法规智能检索系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    text: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    title: str
    content: str
    source_file: str
    score: float


class QueryResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


@app.get("/health")
def health():
    return {"status": "ok", "index_loaded": os.path.exists(INDEX_FILE)}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    results = search(req.text.strip(), top_k=req.top_k or 5)
    return QueryResponse(
        query=req.text,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@app.post("/reindex")
def reindex():
    return {"status": "ok", "message": "索引为预构建，不可重新构建"}


# 前端页面
frontend_index = os.path.join(APP_DIR, "frontend", "index.html")


@app.get("/")
def root():
    return FileResponse(frontend_index)


# ===================== 启动 =====================
import uvicorn


def get_free_port():
    import socket
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


if __name__ == "__main__":
    port = get_free_port()
    print(f"=" * 50)
    print(f"  民航法规智能检索系统")
    print(f"  索引文件: {INDEX_FILE}")
    print(f"  启动地址: http://localhost:{port}")
    print(f"  按 Ctrl+C 停止服务")
    print(f"=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
