FROM ubuntu

WORKDIR /app

RUN apt-get update 

RUN apt-get install -y python3-pip

RUN pip install requests flask numpy sentence_transformers

ADD . /app

EXPOSE 5000

CMD ["python3", "server.py"]

