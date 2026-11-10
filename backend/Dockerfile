FROM python:3.12-slim

WORKDIR /srv

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('intfloat/multilingual-e5-small'); CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')"

COPY backend/ .

RUN python -c "from app.rag.knowledgeBase import obterBaseConhecimento; obterBaseConhecimento()"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:aplicacao --host 0.0.0.0 --port ${PORT:-8000}"]
