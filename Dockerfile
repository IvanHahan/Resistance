FROM python:3.8.5-buster
MAINTAINER 'ivanhahanov@icloud.com'

WORKDIR resistance

COPY . .

RUN pip install --upgrade pip; \
    pip install -r requirements.txt

EXPOSE 5000/tcp

ENTRYPOINT [ "gunicorn", "run:app", "-k=gevent", "-b=0.0.0.0:5000" ]