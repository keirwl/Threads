"""`main` is the top level module for your Flask application."""

# Import the Flask Framework
from flask import Flask, request, render_template, flash, redirect, url_for
from google.appengine.ext import ndb
app = Flask(__name__)
app.debug = True

SECRET_KEY = "b18d7a3ffb55304f3c904c38449072f16d18c8c36ee2c458f271a4e5396572a8"
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

class Post(ndb.Model):
    ident = ndb.IntegerProperty()
    title = ndb.StringProperty(required=True)
    content = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)

@app.route("/")
def index():
    return redirect(url_for("show"))

@app.route('/show')
def show():
    posts = Post.query()
    return render_template("show.html", posts=posts)

@app.route("/add")
def post_form():
    return render_template("post.html")

@app.route("/post", methods=["POST"])
def add_post():
    post = Post(title=request.form["title"], content=request.form["content"])
    post_key = post.put()
    
    return render_template("posted.html", post_key=post_key)

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404


@app.errorhandler(500)
def page_not_found(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
