#!/usr/bin/env python
#
# Simple asynchronous HTTP proxy with tunnelling (CONNECT).
#
# GET/POST proxying based on
# http://groups.google.com/group/python-tornado/msg/7bea08e7a049cf26
#
# Copyright (C) 2012 Senko Rasic <senko.rasic@dobarkod.hr>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient
import tornado.httputil
from tornado import gen
from base import BaseAPIHandler
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

LOGGER = logging.getLogger(__name__)


class Request:
   # _http_client: AsyncHTTPClient

    def __init__(self, http_client = None):
        self._http_client = http_client or AsyncHTTPClient()

    async def resp(self, url, request, callback):
        body = request.body if request.body else None
        method = request.method
        headers = request.headers
        req = HTTPRequest(url=url, method=method, body=body, headers=headers)
        try:
            response = await self._http_client.fetch(req, callback=callback, raise_error=False)
            return response
        except Exception as e:
            LOGGER.info(e)
            return e


class ProxyHandler(BaseAPIHandler):
    SUPPORTED_METHODS = ['GET', 'POST']

    def compute_etag(self):
        return None  # disable tornado Etag

    async def get(self):
        LOGGER.debug('Handle %s request to %s', self.request.method,
                     self.request.uri)
        print('Handle %s request to %s', self.request.method,
                     self.request.uri)

        def handle_response(response):
            if (response.error and not isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code)
                self._headers = tornado.httputil.HTTPHeaders()  # clear tornado default header
                print(2)
                for header, v in response.headers.get_all():
                    if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                        self.add_header(header, v)  # some header appear multiple times, eg 'Set-Cookie'

                if response.body:
                    self.set_header('Content-Length', len(response.body))
                    self.write(response.body)
            self.finish()

        try:
            if 'Proxy-Connection' in self.request.headers:
                del self.request.headers['Proxy-Connection']
            print(3)
            await Request().resp(url=self.request.uri, callback=handle_response, request=self.request)

        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()

    @gen.coroutine
    def post(self):
        return self.get()


def run_proxy(port, start_ioloop=True):
    """
    Run proxy on the specified port. If start_ioloop is True (default),
    the tornado IOLoop will be started immediately.
    """
    app = tornado.web.Application([
        (r'.*', ProxyHandler),
    ])
    app.listen(port)
    ioloop = tornado.ioloop.IOLoop.instance()
    if start_ioloop:
        ioloop.start()


if __name__ == '__main__':
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print("Starting HTTP proxy on port %d" % port)
    run_proxy(port)
