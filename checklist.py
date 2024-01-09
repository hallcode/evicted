import os
import yaml
import datetime
from dateutil.relativedelta import relativedelta
import secrets
from flask import abort


class Checklist:
    # This is a bit of a god class but, this is a simple app so...

    NOTICE_MAP = {
        "s21": {
            "name": "Housing Act 1988, s 21"
        },
        "s8": {
            "name": "Housing Act 1988, s 8"
        }
    }

    def __init__(self, checklist_id=None):
        self.start_time = datetime.datetime.now()
        self.last_change_time = datetime.datetime.now()
        self.responses = []
        self.id = checklist_id

        # Load the responses from disk
        self.load()

        # Load the question set
        self.questions = []
        with open("questions.yaml", "r") as questions_file:
            questions = yaml.safe_load_all(questions_file)
            for question in questions:
                question["field_template"] = f"fields/{question['type']}.html"

                # Load options from file if required
                if "options" in question:
                    if isinstance(question["options"], str):
                        with open(f'./data/{question["options"]}') as yaml_file:
                            options = yaml.safe_load(yaml_file)
                            question['options'] = {}
                            for key, value in options.items():
                                if isinstance(value, str):
                                    question['options'][key] = value
                                else:
                                    question['options'][key] = value['name']

                self.questions.append(question)

        self.set_answered_questions()

    def get_answered_questions(self):
        return list(map(lambda r: r["id"], self.responses))

    def get_response(self, question_id):
        answered_questions = self.get_answered_questions()
        if question_id not in answered_questions:
            return None

        for r in self.responses:
            if r["id"] == question_id:
                return r["value"]

    def set_answered_questions(self):
        answered_questions = self.get_answered_questions()
        for question in self.questions:
            question["answered"] = question["id"] in answered_questions

    def load(self):
        if self.id is None:
            self.id = secrets.token_urlsafe(12)

        path = f'./checklists/{self.id}.yaml'
        try:
            with open(path, "x") as responses_file:
                responses_format = {
                    "start": self.start_time,
                    "last_change": datetime.datetime.now(),
                    "responses": self.responses
                }
                responses_file.write(yaml.safe_dump(responses_format))
        except FileExistsError:
            with open(path, "r") as responses_file:
                responses_format = yaml.safe_load(responses_file)

        self.responses = responses_format["responses"]
        self.start_time = responses_format["start"]
        self.last_change_time = responses_format["last_change"]

        return self.responses

    def save(self):
        if not self.id:
            return

        responses_format = {
            "start": self.start_time,
            "last_change": datetime.datetime.now(),
            "responses": self.responses
        }

        path = f'./checklists/{self.id}.yaml'
        with open(path, "w") as responses_file:
            responses_file.write(yaml.safe_dump(responses_format))

    def get_next_question(self):
        for question in self.questions:
            if question["answered"]:
                continue

            method_name = f'show_{question["id"]}'
            if hasattr(self, method_name):
                should_show = getattr(self, method_name)
                if callable(should_show):
                    if not should_show():
                        continue
                else:
                    if not should_show:
                        continue

            return question["id"]

        return None

    def get_question(self, question_id: str):
        questions = list(filter(lambda q: q["id"] == question_id, self.questions))
        if len(questions) < 1:
            return {}

        return questions[0]

    def add_response(self, **kwargs):
        question_id = kwargs["question_id"]
        questions = list(filter(lambda q: q["id"] == question_id, self.questions))
        if len(questions) < 1:
            abort(400)
        question = questions[0]

        if question["type"] == "date":
            try:
                value = datetime.datetime(year=int(kwargs[f"{question_id}_year"]),
                                          month=int(kwargs[f"{question_id}_month"]),
                                          day=int(kwargs[f"{question_id}_day"])).date()
            except KeyError:
                abort(400)
        else:
            value = kwargs[question["id"]]

        self.responses.append({
            "id": question["id"],
            "value": value
        })
        self.set_answered_questions()

    ############################################################################
    # VALIDATION METHODS
    ############################################################################
    # They must all return True or False

    def show_fixed_term_length(self):
        return self.get_response("fixed_term") == "Y"

    def show_still_fixed_term(self):
        fixed_term = self.get_response("fixed_term")
        if fixed_term != "Y":
            return False

        fixed_term_length = self.get_response("fixed_term_length")
        start_date = self.get_response("start_date")

        now = datetime.date.today()
        end_of_fixed_term = start_date + datetime.timedelta(4 * int(fixed_term_length))
        return now > end_of_fixed_term

    def show_notice_type(self):
        return self.get_response("written_notice")

    def show_section_8_grounds(self):
        return self.get_notice_type()['has_grounds']

    def show_notice_of_ground(self):
        return self.get_response("section_8_grounds")['prior_notice']

    def show_educational_establishment(self):
        return self.get_response("section_8_grounds") == "4"

    def show_date_of_notice(self):
        return self.get_response("written_notice")

    def show_date_received(self):
        return self.get_response("written_notice")

    def show_end_date_yn(self):
        return self.get_response("written_notice")

    def show_end_of_tenancy_date(self):
        written_notice = self.get_response("written_notice")
        end_date_yn = self.get_response("end_date_yn")
        return written_notice and end_date_yn

    def show_reference(self):
        return not self.get_response("is_first_party")

    def show_deposit(self):
        return self.get_response("notice_type") == "s21"

    def show_deposit_amount(self):
        return self.get_response('deposit')

    ############################################################################
    # SPECIAL VALUE GETTERS
    ############################################################################

    def get_s8_ground(self):
        ground = self.get_response("section_8_grounds")
        if ground is None:
            return None

        with open(f'./data/s8grounds.yaml') as yaml_file:
            grounds = yaml.safe_load(yaml_file)
            ground = grounds[ground]

            notice_start = self.get_response('date_of_notice')
            required_notice = {ground["notice"][1]: int(ground["notice"][0])}
            ground["required_notice"] = datetime.timedelta(**required_notice)
            ground["notice_end"] = notice_start + relativedelta(**required_notice)
            ground["notice_okay"] = self.get_response('end_of_tenancy_date') >= ground["notice_end"]

            return ground

    def get_notice_type(self):
        notice_id = self.get_response("notice_type")
        if notice_id is None:
            return None

        with open(f'./data/notice_types.yaml') as yaml_file:
            notices = yaml.safe_load(yaml_file)
            notice = notices[notice_id]

            ground = self.get_s8_ground()
            if ground is not None:
                notice["notice_end"] = ground["notice_end"]
                notice["notice_okay"] = ground["notice_okay"]
                notice["required_notice"] = ground["required_notice"]

            else:
                notice_start = self.get_response('date_of_notice')
                required_notice = {notice["notice"][1]: int(notice["notice"][0])}
                notice["required_notice"] = datetime.timedelta(**required_notice)
                notice["notice_end"] = notice_start + relativedelta(**required_notice)
                notice["notice_okay"] = self.get_response('end_of_tenancy_date') >= notice["notice_end"]

            return notice

    def get_notice_length(self):
        notice = self.get_notice_type()
        notice_start = self.get_response('date_of_notice')
        notice_end = self.get_response('end_of_tenancy_date')

        return notice_end - notice_start
