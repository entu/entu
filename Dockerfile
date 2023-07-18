FROM python:2.7-slim-buster

CMD python -u ./app/main.py --logging=error

WORKDIR /usr/src/entu
COPY ./ ./

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y gcc
RUN pip install -r requirements.txt
