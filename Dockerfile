FROM python:3.10-bullseye
COPY requirements.txt /usr/src/bot/
WORKDIR /usr/src/bot
RUN pip install -r requirements.txt
COPY . .
WORKDIR /usr/src/bot/bot
CMD [ "python3", "cbs.py" ]