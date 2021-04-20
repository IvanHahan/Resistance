FROM python:3.8.5-buster
MAINTAINER 'ivanhahanov@icloud.com'

WORKDIR resistance

COPY . .

RUN pip install --upgrade pip; \
    pip install -r requirements.txt

EXPOSE 5000/tcp

ENV APP_CONFIG='Default'
ENV PORT=5000

CMD gunicorn run:app --worker-class eventlet -b=0.0.0.0:$PORT