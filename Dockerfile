FROM python:3.11-slim-buster

EXPOSE 8501

WORKDIR /usr/src/app 

COPY requirements.txt ./

RUN pip install --upgrade pip --root-user-action=ignore
RUN pip install -r requirements.txt --root-user-action=ignore

ENV PYTHONUNBUFFERED "1"

COPY . /usr/src/app