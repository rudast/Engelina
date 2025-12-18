FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt /app/requirements.txt
#RUN apt-get update && apt-get install -y --no-install-recommends nvidia-utils-535 && rm -rf /var/lib/apt/lists/*
RUN apt-get update
RUN pip install --upgrade pip \
 && pip install --default-timeout=600 -r /app/requirements.txt

COPY src /app/src

# по умолчанию API, runner переопределим в compose
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8002"]
