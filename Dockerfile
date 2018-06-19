FROM python:2.7-slim-jessie

CMD ["python", "/usr/src/entu/app/main.py"]

RUN apt-get update && apt-get install -y build-essential gcc libmysqlclient-dev python-imaging libjpeg-dev zlib1g-dev libpng12-dev

ADD ./ /usr/src/entu

RUN cd /usr/src/entu && pip install -r requirements.txt
