#!/usr/bin/env python3
import os.path

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

define("port", default=8888, help="run server on given port", type=int)

class Application(tornado.web.Application):
    """Base tornado web class for our application."""
    def __init__(self):
        handlers = []
        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)


class Page(RequestHandler):
    """Base class for pages."""
    def fail(self, message):
        """Send error message to be displayed."""
        self.write(message)


def main():
    """Start our web application."""
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
