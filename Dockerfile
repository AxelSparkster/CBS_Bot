FROM python:3.10-bullseye
COPY requirements.txt /app/
RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot
COPY . .
CMD [ "python3", "cbs.py" ]