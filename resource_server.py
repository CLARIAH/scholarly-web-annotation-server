import os
from flask import Flask
from flask.ext.cors import CORS

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('testletter.html'))
cors = CORS(app)

if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 3002)), debug=True)

