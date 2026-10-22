
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the OpenMP runtime required by LightGBM.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src ./src
COPY data/rag/corpus ./data/rag/corpus

# Install CPU-only PyTorch, then the application dependencies.
RUN pip install --upgrade pip \
    && pip install \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
        "torch>=2.5,<3" \
    && python -c "import torch; assert torch.version.cuda is None; print('CPU-only PyTorch:', torch.__version__)" \
    && python -c "import torch; print('torch==' + torch.__version__)" > /tmp/torch-constraints.txt \
    && pip install --constraint /tmp/torch-constraints.txt ".[ml,nlp,llm]" \
    && python -c "import torch; assert torch.version.cuda is None; import lightgbm; print('Verified PyTorch and LightGBM imports')"

EXPOSE 8000

CMD ["uvicorn", "financial_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
