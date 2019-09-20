#!/usr/bin/env python

import unittest
import urllib.request
import subprocess
import os
import time

import tornado.ioloop
import tornado.httpclient

import sys
from tornado_proxy.proxy import run_proxy
from tornado.testing import AsyncHTTPTestCase
from tornado.testing import gen_test

sys.path.append('../')


class TestStandaloneProxy(AsyncHTTPTestCase):
    def setUp(self):
        self.proxy = subprocess.Popen(['python', 'tornado_proxy/proxy.py',
            '8888'])
        proxy_support = urllib.request.ProxyHandler({
            "https": "http://localhost:8888",
            "http": "http://localhost:8888"
        })
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        # make sure the subprocess started listening on the port
        time.sleep(1)

    def tearDown(self):
        os.kill(self.proxy.pid, 15)
        time.sleep(1)
        os.kill(self.proxy.pid, 9)

    def test(self):
        base_url = '//httpbin.org/'
        #urllib.request.urlopen('https:' + base_url + 'get').read()
        urllib.request.urlopen('http:' + base_url + 'get').read()
        #urllib.request.urlopen('https:' + base_url + 'post', '').read()
        #urllib.request.urlopen('http:' + base_url + 'post', '').read()


class TestTornadoProxy(AsyncHTTPTestCase):
    def setUp(self):
        self.io_loop = tornado.ioloop.IOLoop.current()
        run_proxy(8889, start_ioloop=False)

    def tearDown(self):
        pass

    @gen_test
    def test(self):
        def handle_response(resp):
            self.assertIsNone(resp.error)
            self.io_loop.stop()

        tornado.httpclient.AsyncHTTPClient.configure(
            "tornado.curl_httpclient.CurlAsyncHTTPClient")
        client = tornado.httpclient.AsyncHTTPClient()

        req = tornado.httpclient.HTTPRequest('http://httpbin.org/',
            proxy_host='127.0.0.1', proxy_port=8889)
        http_response = yield client.fetch(req)

        req = tornado.httpclient.HTTPRequest('http://httpbin.org/',
            proxy_host='127.0.0.1', proxy_port=8889)
        client.fetch(req, handle_response)
        self.io_loop.start()


if __name__ == '__main__':
    unittest.main()
