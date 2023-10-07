"""URL router for the web server."""

import json
import re
from urllib.parse import urlparse, parse_qs


class Router:
    def __init__(self):
        self.routes = []

    def route(self, method, pattern):
        def decorator(fn):
            regex = re.compile("^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern) + "$")
            self.routes.append((method, regex, fn))
            return fn
        return decorator

    def get(self, pattern):
        return self.route("GET", pattern)

    def post(self, pattern):
        return self.route("POST", pattern)

    def resolve(self, method, path):
        for route_method, regex, fn in self.routes:
            if route_method == method:
                m = regex.match(path)
                if m:
                    return fn, m.groupdict()
        return None, {}
