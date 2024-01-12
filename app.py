import datetime
import markdown
from flask import Flask, render_template
import modules.checklist
from utils import time_ago, notice_period, to_title


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=b"this-is-my-secret-key",
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.register_blueprint(modules.checklist.checklist_bp)

    app.add_template_filter(notice_period)
    app.add_template_filter(time_ago)
    app.add_template_filter(to_title)

    @app.get("/")
    def index():
        return render_template("home.html", page_title="Home")

    return app


if __name__ == "__main__":
    app.run()
