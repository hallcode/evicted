import datetime

import markdown
from flask import Flask, render_template, redirect, url_for, request, abort, session
from checklist import Checklist

app = Flask(__name__)
app.secret_key = b'this-is-my-secret-key'


@app.get('/')
def index():
    return render_template("home.html", page_title="Home")


@app.get('/checklist')
def pre_check():
    with open("./static/before-you-start.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()
        html = markdown.markdown(text)
        return render_template("start.html", page_title="Before you start", body_text=html)


@app.get('/checklist/start')
def create_checklist():
    # Create unique ID
    checklist = Checklist()
    session["checklist_id"] = checklist.id

    return redirect(url_for("question",
                            question_id=checklist.get_next_question(),
                            checklist_id=checklist.id))


@app.get('/checklist/<checklist_id>/results')
def results(checklist_id):
    try:
        if session["checklist_id"] != checklist_id:
            abort(404)
    except KeyError:
        abort(404)

    checklist = Checklist(checklist_id)

    return render_template("results.html", checklist=checklist, page_title="Your results")


@app.get('/checklist/<checklist_id>/<question_id>')
def question(checklist_id, question_id):
    try:
        if session["checklist_id"] != checklist_id:
            abort(404)
    except KeyError:
        abort(404)

    checklist = Checklist(checklist_id)
    this_question = checklist.get_question(question_id)
    return render_template("question.html",
                           page_title=this_question["label"],
                           question=this_question,
                           checklist=checklist)


@app.post('/checklist/<checklist_id>/save')
def save_response(checklist_id):
    try:
        if session["checklist_id"] != checklist_id:
            abort(404)
    except KeyError:
        abort(404)

    checklist = Checklist(checklist_id)

    checklist.add_response(**request.form)
    checklist.save()

    next_question_id = checklist.get_next_question()
    if next_question_id is None:
        return redirect(url_for("results", checklist_id=checklist.id))

    return redirect(url_for("question",
                            question_id=next_question_id,
                            checklist_id=checklist.id))


@app.template_filter()
def time_ago(value):
    if not isinstance(value, datetime.date):
        raise ValueError

    # We want them both to be timestamps so we can compare without errors
    now = datetime.datetime.now()
    then = datetime.datetime.fromisoformat(value.isoformat())

    delta: datetime.timedelta = now - then
    if delta.days < 28:
        return f"{round(delta.days, 0)} days ago"

    if delta.days < 365:
        months = delta.days / 28
        return f"{round(months, 0)} months ago"

    years = delta.days / 365
    return f"{round(years, 2)} years ago"


@app.template_filter()
def notice_period(notice_duration):
    if notice_duration.days < 7:
        return f"{notice_duration.days:3.1f} days"

    if notice_duration.days < 28:
        d = notice_duration.days / 7
        return f"{d:3.1f} weeks"

    m = notice_duration.days / 28
    return f"{m:0.0f} months"


if __name__ == '__main__':
    app.run()
