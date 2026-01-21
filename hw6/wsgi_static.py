import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(BASE_DIR, "static", "sample.html")

def app(environ, start_response):
    with open(SAMPLE, "rb") as f:
        data = f.read()
    start_response("200 OK", [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(data))),
    ])
    return [data]
