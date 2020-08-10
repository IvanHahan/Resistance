FROM python:3.8.5-buster
MAINTAINER 'ivanhahanov@icloud.com'

WORKDIR resistance

COPY . .

RUN pip install --upgrade pip; \
    pip install -r requirements.txt

EXPOSE 5000/tcp

ENTRYPOINT [ "gunicorn", "run:app", "-k=gevent", "-b=192.168.0.102:5000" ]