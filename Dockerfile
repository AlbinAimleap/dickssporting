FROM python:3.11-slim

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install --upgrade pip

RUN pip install --upgrade numpy pandas tls_client typing_extensions

CMD ["sh", "-c", "python /usr/src/app/main.py -I $INPUT_FILE"]