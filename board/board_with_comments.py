"""A simple URL shortener using Werkzeug and redis."""
import os
from datetime import datetime
from createdb import BoardDataBase
import redis
from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug import run_simple
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.urls import url_parse
from werkzeug.utils import redirect
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response


def get_hostname(url):
    return url_parse(url).netloc


class BoardWithComments:
    def __init__(self, config):
        self.database_worker = BoardDataBase()
        self.redis = redis.Redis(config["redis_host"], config["redis_port"])
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path), autoescape=True
        )
        self.jinja_env.filters["hostname"] = get_hostname

        self.url_map = Map(
            [
                Rule("/", endpoint="layout"),
                Rule("/new_post", endpoint="new_post"),
                Rule("/<id>", endpoint="post_info"),
            ]
        )

    def on_layout(self, request):
        post_list = list()
        for post in self.database_worker.get_posts():
            posts = dict()
            posts['title'] = post[2]
            posts['text'] = post[1]
            posts['id'] = post[0]
            post_list.append(posts)
        return self.render_template("layout.html", posts=post_list)

    def on_post_info(self, request, id):
        post_info = self.database_worker.get_post_info(id)
        post = dict()
        comments = list()
        post['datetime'] = post_info[3][:10]
        post['title'] = post_info[2]
        post['author'] = post_info[1]
        post['text'] = post_info[0]
        for cmnt in self.database_worker.get_comments(id):
            comment_dict = dict()
            comment_dict['author'] = cmnt[1]
            comment_dict['text'] = cmnt[0]
            comments.append(comment_dict)
        if request.method == "POST":
            author = request.form["author"]
            text = request.form["text"]
            self.database_worker.add_comment(author=author, text=text, board_id=id)
            return redirect(f"/{id}")
        return self.render_template("post_details.html", post=post, comments=comments)

    def on_new_post(self, request):
        error = None
        url = ""
        if request.method == "POST":
            author = request.form["author"]
            title = request.form["title"]
            text = request.form["text"]
            self.database_worker.add_post(text=text, author=author, title=title,
                                          now_time=datetime.now())
            return redirect("/")
        return self.render_template("new_post.html", error=error, url=url)

    def error_404(self):
        response = self.render_template("404.html")
        response.status_code = 404
        return response

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype="text/html")

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, f"on_{endpoint}")(request, **values)
        except NotFound:
            return self.error_404()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(redis_host="localhost", redis_port=6379, with_static=True):
    app = BoardWithComments({"redis_host": redis_host, "redis_port": redis_port})
    if with_static:
        app.wsgi_app = SharedDataMiddleware(
            app.wsgi_app, {"/static": os.path.join(os.path.dirname(__file__), "static")}
        )
    return app


if __name__ == "__main__":
    app = create_app()
    run_simple("127.0.0.1", 5000, app, use_debugger=True, use_reloader=True)
