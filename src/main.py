#!/usr/bin/env python3
import os.path
from os import urandom

import pymongo
import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.web import (authenticated)
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
    """Homepage of the website."""
    def get(self):
        self.render("index.html")


class PostPage(Page):
    """A post shown individually."""
    def get(self, slug):
        entry = db.posts.find_one({"slug": slug})
        if not entry: raise tornado.web.HTTPError(404)
        self.render("post.html", post=entry)


class PostsPage(Page):
    """List of all of our posts."""
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


class AdminLoginPage(Page):
    """Logs in the the admin into the control panel."""
    def get(self):
        self.render("login.html")

    
class AdminPage(Page):
    """Index for our admin panel."""
    @authenticated
    def get(self):
        self.render("admin.html")

    
def main():
    """Create and start our web application."""
    tornado.options.parse_command_line()
    join = os.path.join

    settings = dict(
        cookie_secret=urandom(64),
        xsrf_cookies=True,
        template_path=join(current_dir, "templates"),
        static_path=join(current_dir, "static"),
        login_url="/admin/login",
        debug=True,
    )

    handlers = [
        (r"/", IndexPage),
        (r"/posts", PostsPage),
        (r"/post/([^/]+)", PostPage),
        (r"/admin", AdminPage),
        (r"/admin/login", AdminLoginPage),
    ]

    application = tornado.web.Application(handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
