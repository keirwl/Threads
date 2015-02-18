from flask import Flask, request, render_template, flash, redirect, url_for, abort
from base64 import b32encode, urlsafe_b64encode, urlsafe_b64decode
from flask_markdown import markdown
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from google.appengine.ext import ndb
from hashlib import md5
import os
app = Flask(__name__)
app.debug = True
Bootstrap(app)
markdown(app)

# I'm not sure why we need this, but we do
SECRET_KEY = "b18d7a3ffb55304f3c904c38449072f16d18c8c36ee2c458f271a4e5396572a8"

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

class Post(ndb.Model):
    ident = ndb.IntegerProperty()
    content = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.StringProperty(required=True)

class Thread(ndb.Model):
    ident = ndb.StringProperty(required=True)
    salt = ndb.StringProperty(required=True)
    title = ndb.StringProperty(required=True)
    op = ndb.StructuredProperty(Post, required=True)
    num_posts = ndb.IntegerProperty(required=True, default=1)

# This and the next function override url_for to append the 
# last updated time to static file urls, preventing browser
# caching from being annoying during testing.
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

def salt():
    "Returns a random 64-bit number as a b64-encoded string."
    return urlsafe_b64encode(os.urandom(8)).decode()

def ident():
    "Returns a random 8-char b32 string."
    return b32encode(os.urandom(5)).decode()

def author_identity(passkey, salt):
    return urlsafe_b64encode(md5(passkey+salt).digest()).decode()[:8]

@app.route('/')
def show():
    threads = Thread.query()
    return render_template("show.html", threads=threads)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/<thread_ident>")
def show_thread(thread_ident):
    thread = Thread.query(Thread.ident == thread_ident).get()
    if thread == None: abort(404)
    posts = Post.query(ancestor=thread.key).fetch()
    return render_template("thread.html", thread=thread, posts=posts, num=len(posts))

@app.route("/<thread_ident>/post", methods=["POST"])
def add_post(thread_ident):
    thread_key = ndb.Key(urlsafe=request.form["urlkey"])
    post = Post(content=request.form["content"], parent=thread_key)
    thread = thread_key.get()

    if request.form["author"] == "":
        post.author = "Anonymous"
    else:
        post.author = author_identity(request.form["author"], thread.salt)

    post_key = post.put()
    thread.num_posts += 1
    thread.put()

    return redirect(url_for('show_thread', thread_ident=thread_ident))

@app.route("/add")
def post_form():
    return render_template("post.html")

@app.route("/post", methods=["POST"])
def add_thread():
    thread = Thread(ident=ident(), salt=salt(), title=request.form["title"],
        op=Post(content=request.form["content"], ident=1))

    if request.form["author"] == "":
        thread.op.author = "Anonymous"
    else:
        thread.op.author = author_identity(request.form["author"], thread.salt)
    thread_key = thread.put()
    return render_template("posted.html", return_url=url_for('show_thread', thread_ident=thread.ident))


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404


@app.errorhandler(500)
def page_not_found(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
