import os
from flask import Flask

app = Flask(__name__)


@app.route("/health")
def health():
    return '{"status": "ok"}'


@app.route("/version")
def version():
    return '{"version": "1.0"}'


@app.route("/")
def hello():
    return " ".join(["Hello world from", os.environ["HOSTNAME"], "!"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="80")
