# ai-vocabulary-builder Dockerfile

FROM python:3.13-slim
WORKDIR /app

VOLUME /data
ENV AIVOC_DATA_DIR=/data

RUN pip install ai-vocabulary-builder

EXPOSE 16093

CMD ["aivoc", "notebook" , "--host", "0.0.0.0"]
