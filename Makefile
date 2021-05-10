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


clariah_demo:
	rm -rf clariah_app
	cp -r app clariah_app
	cp demo_init.py clariah_app/apis/
	mv clariah_app/apis/__init__.py clariah_app/apis/orig_init.py
	mv clariah_app/apis/demo_init.py clariah_app/apis/__init__.py
	cp demos_api.py clariah_app/apis/
	mv clariah_app/apis/demos_api.py clariah_app/apis/demos.py
	cp -r demos/* clariah_app/public/demos/
