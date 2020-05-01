from typing import Dict, Union
from flask import Flask, json
from flask_cors import CORS

from apis import blueprint as api
from apis.user import configure_store as configure_user_store
from apis.annotation import configure_store as configure_annotation_store
from apis.collection import configure_store as configure_collection_store
from settings import server_config

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('index.html'))
app.add_url_rule('/api', 'api_versions', lambda: app.send_static_file('index.html'))
app.add_url_rule('/favicon.ico', 'favicon', lambda: app.send_static_file('favicon.ico'))
app.add_url_rule('/robots.txt', 'robots', lambda: app.send_static_file('robots.txt'))
app.add_url_rule('/ns/swao', 'swao', lambda: app.send_static_file('vocabularies/index.html'))
app.config['SECRET_KEY'] = "some combination of key words"
cors = CORS(app)

app.register_blueprint(api, url_prefix=server_config['SWAServer']['api_prefix'])


def configure_stores(config: Dict[str, Union[str, int]]):
    configure_user_store(config)
    configure_annotation_store(config)
    configure_collection_store(config)


"""--------------- Ontology endpoints ------------------"""


@app.route("/ns/swao.jsonld", endpoint="swao-jsonld")
def swao():
    with open('./public/vocabularies/swao.json', 'rt') as fh:
        swao_json = json.load(fh)
        return swao_json


if __name__ == "__main__":
    swas_host = server_config["SWAServer"]["host"]
    swas_port = server_config["SWAServer"]["port"]
    app.run(host=swas_host, port=swas_port, debug=True, threaded=True)
