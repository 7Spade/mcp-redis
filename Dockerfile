FROM python:3.13-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade uv

WORKDIR /app
COPY . /app

# 安裝依賴，包括 FastAPI 和 uvicorn
RUN --mount=type=cache,target=/root/.cache/uv \
    uv add fastapi uvicorn[standard] && \
    uv sync --locked

# 暴露端口
EXPOSE 8080

# 設置環境變量
ENV HOST=0.0.0.0
ENV PORT=8080

CMD ["uv", "run", "python", "src/http_server.py"]
