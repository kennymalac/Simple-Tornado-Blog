#!/usr/bin/env python3
import os.path

import pymongo
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

define("port", default=8888, help="run server on given port", type=int)

current_dir = os.path.dirname(__file__)
client = pymongo.MongoClient()
db = client["tornado-blog"]


class Page(tornado.web.RequestHandler):
    """Base class for pages."""
    def fail(self, message):
        """Send error message to be displayed."""
        self.write(message)


class IndexPage(Page):
    def get(self):
        self.render("index.html")


class PostsPage(Page):
    def compile_posts(self, page_num):
        pagination = 10
        db.posts.ensure_index("timestamp", -1)
        return db.posts.find().sort("timestamp", -1).skip(page_num * pagination).limit(pagination)

    def get(self, page_num=1):
        index = page_num - 1
        self.render(
                "posts.html",
                posts=self.compile_posts(index)
        )


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
        (r"/posts", PostsPage),
    ]

    application = tornado.web.Application(handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
