#!/usr/bin/env python3
import os.path

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

current_dir = os.path.dirname(__file__)
define("port", default=8888, help="run server on given port", type=int)


class Page(tornado.web.RequestHandler):
    """Base class for pages."""
    def fail(self, message):
        """Send error message to be displayed."""
        self.write(message)


class IndexPage(Page):
    def get(self):
        self.render("index.html")


def main():
    """Create and start our web application."""
    tornado.options.parse_command_line()
    join = os.path.join

    settings = dict(
        template_path=join(current_dir, "templates"),
        static_path=join(current_dir, "static"),
        debug=True,
    )

    handlers = [
        (r"/", IndexPage),
    ]

    application = tornado.web.Application(handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
