#!/usr/bin/env python3
import os.path
from os import urandom

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.web import (authenticated)
from tornado.options import define, options

import re
from datetime import datetime
import pymongo
from passlib.context import CryptContext

define("port", default=8888, help="run server on given port", type=int)

current_dir = os.path.dirname(__file__)
client = pymongo.MongoClient()
db = client["tornado-blog"]
cryptctx = CryptContext(schemes=["sha256_crypt"])


def slugify(title):
    # remove non-alphanumeric characters
    abc = re.sub(r'\W+', '-', title)
    return abc.lower()


class Page(tornado.web.RequestHandler):
    """Base class for pages."""
    def get_current_user(self):
        """Enables authentication by overriding tornado default."""
        return self.get_secure_cookie("username")
    
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
    def post(self):
        username = self.get_argument("login")
        password = self.get_argument("password")

        if username and password:
            exists = db.users.find_one({"username": username})

            if exists:
                hash1 = exists["password"]
                
                if cryptctx.verify(password, hash1):
                    self.set_secure_cookie("username", username)
                    self.redirect("/admin")
                else:
                    self.fail("Password is incorrect.")
            else:
                self.fail("User does not exist.")
        else:
            self.fail("A username or password was not supplied.")

    def get(self):
        self.render("login.html")

    
class AdminPage(Page):
    """Index for our admin panel."""
    @authenticated
    def get(self):
        self.render("admin.html")


class NewPostPage(Page):
    """Page for creating new posts."""
    @authenticated
    def post(self):
        ga = self.get_argument
        title = ga("title")
        tags = ga("tags")
        body = ga("content")

        if title and tags and body:
            slug = slugify(title)
            
            db.posts.insert(dict(
                title=title,
                author=self.get_current_user(),
                slug=slug,
                timestamp=datetime.now(),
                body=body,
                tags=tags.split(","),
            ))
            self.redirect("/post/" + slug)
        else:
            self.fail("You did not provide all fields!")
        

    @authenticated
    def get(self):
        self.render("newpost.html")


class NewUserPage(Page):
    """Page for creating new users."""
    @authenticated
    def post(self):
        login = self.get_argument("login")
        password = self.get_argument("password")

        #will return nothing if doesn't exist already
        exists = db.users.find_one({"username": login})

        if login and password:
            if not exists:
                db.users.insert(dict(
                    username=login,
                    password=cryptctx.encrypt(password),
                ))
                self.redirect("/admin")
            else:
                self.fail("Login with that username already exists!")
        else:
            self.fail("Please provide both a username and password.")

    def get(self):
        self.render("newuser.html")

    
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
        (r"/admin/newpost", NewPostPage),
        (r"/admin/newuser", NewUserPage),
    ]

    application = tornado.web.Application(handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
