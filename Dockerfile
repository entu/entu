FROM python:2.7-jessie

CMD ["python", "/usr/src/entu/app/main.py"]

WORKDIR /usr/src/entu

COPY ./ ./

RUN pip install -r requirements.txt
