import datetime

from flask import (
    Blueprint,
    render_template,
    session,
    url_for,
    redirect,
    abort,
    request,
    current_app as app,
)
import markdown
from checklist import Checklist

checklist_bp = Blueprint("checklist", __name__, url_prefix="/checklist")


@checklist_bp.get("/")
def pre_check():
    with open("./static/before-you-start.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()
        html = markdown.markdown(text)
        return render_template(
            "start.html", page_title="Before you start", body_text=html
        )


@checklist_bp.get("/start")
def create_checklist():
    # Create unique ID
    checklist = Checklist()
    session["checklist_id"] = checklist.id

    return redirect(
        url_for(
            "checklist.question",
            question_id=checklist.get_next_question(),
            checklist_id=checklist.id,
        )
    )


@checklist_bp.get("/<checklist_id>/results")
def results(checklist_id):
    try:
        if session["checklist_id"] != checklist_id:
            abort(404)
    except KeyError:
        abort(404)

    checklist = Checklist(checklist_id)

    return render_template(
        "results.html", checklist=checklist, page_title="Your results"
    )


@checklist_bp.get("/<checklist_id>/<question_id>")
def question(checklist_id, question_id):
    try:
        if session["checklist_id"] != checklist_id:
            abort(404)
    except KeyError:
        abort(404)

    checklist = Checklist(checklist_id)
    this_question = checklist.get_question(question_id)
    return render_template(
        "question.html",
        page_title=this_question["label"],
        question=this_question,
        checklist=checklist,
    )


@checklist_bp.post("/<checklist_id>/save")
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
        return redirect(url_for("checklist.results", checklist_id=checklist.id))

    return redirect(
        url_for("checklist.question", question_id=next_question_id, checklist_id=checklist.id)
    )
