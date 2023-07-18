FROM python:2.7

CMD python -u ./app/main.py --logging=error

WORKDIR /usr/src/entu
COPY ./ ./

RUN apt-get update
RUN apt-get upgrade -y
RUN pip install -r requirements.txt
