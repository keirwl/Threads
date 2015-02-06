"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import Flask, request, render_template, flash, redirect, url_for, abort
from base64 import b32encode, urlsafe_b64encode, urlsafe_b64decode
from os import urandom
from google.appengine.ext import ndb
app = Flask(__name__)
app.debug = True

SECRET_KEY = "b18d7a3ffb55304f3c904c38449072f16d18c8c36ee2c458f271a4e5396572a8"
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

class Post(ndb.Model):
    ident = ndb.IntegerProperty()
    content = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)

class Thread(ndb.Model):
    ident = ndb.StringProperty(required=True)
    salt = ndb.StringProperty(required=True)
    title = ndb.StringProperty(required=True)
    op = ndb.StructuredProperty(Post, required=True)

def salt():
    return urlsafe_b64encode(urandom(64)).decode()

def ident():
    return b32encode(urandom(5)).decode()

@app.route("/")
def index():
    return redirect(url_for("show"))

@app.route('/show')
def show():
    threads = Thread.query()
    return render_template("show.html", threads=threads)

@app.route("/<thread_ident>")
def show_thread(thread_ident):
    thread = Thread.query(Thread.ident == thread_ident).get()
    if thread == None: abort(404)
    posts = Post.query(ancestor=thread.key).fetch()
    return render_template("thread.html", thread=thread, posts=posts, num=len(posts))

@app.route("/<thread_ident>/post", methods=["POST"])
def add_post(thread_ident):
    thread_key = ndb.Key(urlsafe=request.form["urlkey"])
    post_key = Post(content=request.form["content"], parent=thread_key).put()

    return render_template("posted.html", ident="", return_url="../"+thread_ident)

@app.route("/add")
def post_form():
    return render_template("post.html")

@app.route("/post", methods=["POST"])
def add_thread():
    thread = Thread(ident=ident(), salt=salt(), title=request.form["title"],
        op=Post(content=request.form["content"], ident=1))
    thread_key = thread.put()

    return render_template("posted.html", ident=thread.ident, return_url="show")

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404


@app.errorhandler(500)
def page_not_found(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
