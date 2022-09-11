from waitress import serve
from _3RStore import app

if __name__ == "__main__":
    serve(app, port=8081, url_scheme='https')
