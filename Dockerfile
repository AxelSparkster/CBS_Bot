FROM python:3.10-bullseye
COPY requirements.txt /usr/src/bot/
WORKDIR /usr/src/bot
ENV PYHTONUNBUFFERED=1
RUN apt-get update && apt-get -y install tesseract-ocr
RUN pip install -r requirements.txt
COPY . .
CMD [ "python3", "main.py" ]