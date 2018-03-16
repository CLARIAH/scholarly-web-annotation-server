# Python server for scholarly web annotations

An experimental Python Flask RESTplus server based on the W3C Web Annotation standard, that implements both the [WA data model](https://www.w3.org/TR/annotation-model/) and the [WA protocol](https://www.w3.org/TR/annotation-protocol/). It is developed in tandem with the [Scholarly Web Annotation Client](https://github.com/CLARIAH/scholarly-web-annotation-client) and will eventually be replaced by a proper annotation server.

The server uses [Elasticsearch](https://www.elastic.co/products/elasticsearch) for storage and retrieval of annotations. When running the SWA server, make sure you have a running Elasticsearch instance. Configuration of the Elasticsearch server is done in `settings.py`. This repository contains a file `settings-example.py` that shows how to configure the connection to Elasticsearch. Rename or copy this to `settings.py` to make sure the SWA server can read the configuration file.

## How to install

Clone the repository:
```
git clone https://github.com/marijnkoolen/scholarly-web-annotation-server.git
```

Install the required python packages (for pipenv see https://docs.pipenv.org/):
```
pipenv install
```

## How to run

Start the server:
```
python annotation_server.py
```

and point your browser to `localhost:3000`

## How to modify

Run all tests:
```
make test_server
```
