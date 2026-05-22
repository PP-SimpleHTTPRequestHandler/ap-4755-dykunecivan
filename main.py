import json
from http.server import HTTPServer, BaseHTTPRequestHandler

INITIAL_USERS_LIST = [
    {
        "id": 1,
        "username": "theUser",
        "firstName": "John",
        "lastName": "James",
        "email": "john@email.com",
        "password": "12345",
    }
]

USERS_LIST = INITIAL_USERS_LIST.copy()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self, status_code=200, body=None):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body if body is not None else {}).encode("utf-8"))

    def _pars_body(self):
        content_length = int(self.headers["Content-Length"])
        return json.loads(self.rfile.read(content_length).decode("utf-8"))

    def _is_valid_user_for_post(self, user):
        required_fields = {
            "id": int,
            "username": str,
            "firstName": str,
            "lastName": str,
            "email": str,
            "password": str,
        }

        return (
            isinstance(user, dict)
            and len(user) == len(required_fields)
            and all(field in user and isinstance(user[field], field_type)
                    for field, field_type in required_fields.items())
        )

    def _is_valid_user_for_put(self, user):
        required_fields = {
            "username": str,
            "firstName": str,
            "lastName": str,
            "email": str,
            "password": str,
        }

        return (
            isinstance(user, dict)
            and len(user) == len(required_fields)
            and all(field in user and isinstance(user[field], field_type)
                    for field, field_type in required_fields.items())
        )

    def do_GET(self):
        global USERS_LIST

        if self.path == "/reset":
            USERS_LIST = INITIAL_USERS_LIST.copy()
            self._set_response(200, USERS_LIST)
            return

        if self.path == "/users":
            self._set_response(200, USERS_LIST)
            return

        if self.path.startswith("/user/"):
            username = self.path.split("/user/")[1]

            for user in USERS_LIST:
                if user["username"] == username:
                    self._set_response(200, user)
                    return

            self._set_response(400, {"error": "User not found"})
            return

        self._set_response(404, {})

    def do_POST(self):
        global USERS_LIST

        try:
            body = self._pars_body()
        except Exception:
            self._set_response(400, {})
            return

        if self.path == "/user":
            if not self._is_valid_user_for_post(body):
                self._set_response(400, {})
                return

            if any(user["id"] == body["id"] for user in USERS_LIST):
                self._set_response(400, {})
                return

            USERS_LIST.append(body)
            self._set_response(201, body)
            return

        if self.path == "/user/createWithList":
            if not isinstance(body, list):
                self._set_response(400, {})
                return

            if not all(self._is_valid_user_for_post(user) for user in body):
                self._set_response(400, {})
                return

            existing_ids = [user["id"] for user in USERS_LIST]
            new_ids = [user["id"] for user in body]

            if any(user_id in existing_ids for user_id in new_ids):
                self._set_response(400, {})
                return

            USERS_LIST.extend(body)
            self._set_response(201, body)
            return

        self._set_response(404, {})

    def do_PUT(self):
        try:
            body = self._pars_body()
        except Exception:
            self._set_response(400, {"error": "not valid request data"})
            return

        if not self.path.startswith("/user/"):
            self._set_response(404, {})
            return

        if not self._is_valid_user_for_put(body):
            self._set_response(400, {"error": "not valid request data"})
            return

        try:
            user_id = int(self.path.split("/user/")[1])
        except ValueError:
            self._set_response(404, {"error": "User not found"})
            return

        for user in USERS_LIST:
            if user["id"] == user_id:
                user.update(body)
                self._set_response(200, user)
                return

        self._set_response(404, {"error": "User not found"})

    def do_DELETE(self):
        global USERS_LIST

        if not self.path.startswith("/user/"):
            self._set_response(404, {})
            return

        try:
            user_id = int(self.path.split("/user/")[1])
        except ValueError:
            self._set_response(404, {"error": "User not found"})
            return

        for user in USERS_LIST:
            if user["id"] == user_id:
                USERS_LIST.remove(user)
                self._set_response(200, {})
                return

        self._set_response(404, {"error": "User not found"})


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, host="localhost", port=8000):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()