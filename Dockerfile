FROM python:2.7-slim-jessie

CMD ["python", "/usr/src/entu/app/main.py"]

WORKDIR /usr/src/entu

RUN apt-get install -y --force-yes build-essential gcc python-imaging libjpeg-dev zlib1g-dev libpng12-dev libmysqlclient-dev

COPY ./ /usr/src/entu

RUN pip install -r requirements.txt
