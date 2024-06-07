FROM python:3.10-bullseye
COPY requirements.txt /usr/src/bot/
WORKDIR /usr/src/bot
RUN pip install -r requirements.txt
COPY . .
CMD [ "python3", "main.py" ]