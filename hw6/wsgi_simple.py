from urllib.parse import parse_qs

def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()

    get_params = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)

    post_params = {}
    if method == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(length).decode("utf-8", "replace")
        post_params = parse_qs(body, keep_blank_values=True)

    payload = (
        "WSGI SIMPLE APP\n"
        f"METHOD: {method}\n\n"
        f"GET: {get_params}\n"
        f"POST: {post_params}\n"
    )

    # делаем ответ примерно 2KB (для бенчей)
    target = 2048
    b = payload.encode("utf-8")
    if len(b) < target:
        payload += "\n" + ("." * (target - len(b)))

    data = payload.encode("utf-8")
    start_response("200 OK", [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(data))),
    ])
    return [data]
