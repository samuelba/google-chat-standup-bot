FROM alpine:latest

RUN apk add --no-cache bash python3 python3-dev py3-pip gcc musl-dev postgresql-dev tzdata && \
    pip3 install --no-cache --upgrade setuptools \
         Flask flask-restful \
         google-api-python-client \
         httplib2 \
         psycopg2

ENV CRON_CMD /usr/bin/python3 /root/bot/trigger_standup_dialog.py
ENV TIMESTAMP false
ENV CRONFILE /etc/crontabs/root
ENV LOGS_DIR /root/logs

COPY bot /root/bot
COPY entrypoint.sh /root
COPY credentials /root/credentials

EXPOSE 5000
STOPSIGNAL SIGINT

WORKDIR /root
ENV PYTHONPATH "${PYTHONPATH}:/root"
ENTRYPOINT ["/bin/bash", "/root/entrypoint.sh"]
