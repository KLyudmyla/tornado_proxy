from tornado.util import ObjectDict
from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_default_headers(self):
        super(BaseHandler, self).set_default_headers()
        self.set_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        )
        self.set_header(
            "Access-Control-Allow-Headers", "authorization, X-AUTH-TOKEN, content-type"
        )
        self.set_header("Access-Control-Allow-Credentials", "true")



class BaseAPIHandler(BaseHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_object = ObjectDict()

