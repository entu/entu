FROM python:2.7-slim

ADD ./ /usr/src/entu
RUN apt-get update && apt-get install -y build-essential gcc libmysqlclient-dev python-imaging libjpeg-dev zlib1g-dev libpng12-dev
RUN pip install beautifulsoup4 boto chardet markdown2 mistune mysql-python newrelic pillow python-dateutil PyYAML raven SimpleAES suds tornado torndb xmltodict

CMD ["python", "/usr/src/entu/app/main.py"]
