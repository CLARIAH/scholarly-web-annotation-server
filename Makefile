all: build start

build:
	#sudo docker build --no-cache -t annotation-uwsgi-nginx-flask .
	sudo docker build --no-cache -t annotation-uwsgi-flask .

start:
	#sudo docker run -d --name annotation-uwsgi-nginx-flask --expose 80 --net nginxproxynetwork -e VIRTUAL_HOST=nginxproxy.localhost annotation-uwsgi-nginx-flask
	sudo docker run -d --name annotation-uwsgi-flask --expose 8080 --net nginxproxynetwork -e VIRTUAL_HOST=annotation.clariah.nl annotation-uwsgi-flask

start_alt:
	sudo docker run -d --name annotation-uwsgi-nginx-flask -p 80:80 annotation-uwsgi-nginx-flask

stop:
	#sudo docker stop annotation-uwsgi-nginx-flask
	sudo docker stop annotation-uwsgi-flask

remove:
	#sudo docker rm annotation-uwsgi-nginx-flask
	sudo docker rm annotation-uwsgi-flask
