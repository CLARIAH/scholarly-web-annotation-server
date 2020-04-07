FROM tiangolo/uwsgi-nginx-flask:python3.7

ENV UWSGI_INI /app/uwsgi.ini

ENV LISTEN_PORT 80

EXPOSE 80

COPY ./app /app

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install -r requirements.txt

