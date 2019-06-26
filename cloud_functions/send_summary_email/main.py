import os
import datetime
import pytz
import jinja2
import sendgrid
from sendgrid.helpers.mail import Content, Mail, To, Subject, From, Personalization
from google.cloud import datastore
from python_http_client import exceptions

TEMPLATE_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
IS_DEVELOPMENT = os.environ.get('ACCOUNTABOT_ENVIRONMENT', 'prod').lower() == 'development'
DEVELOPER_EMAIL_STRING = 'danfrankj'


def compute_goal_color(goal):
    if goal['denominator'] == 0:
        return ''
    ratio = goal['progress'] / goal['denominator']
    if ratio >= 0.9:
        return '#10BA66'
    if ratio >= .7:
        return '#81C42A'
    if ratio >= .5:
        return '#F4E015'
    return '#F6C504'


def send_summary_email(data, context):
    print(data, context)
    force_send = data.get('force_send', False)
    sg = sendgrid.SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
    dt = datetime.datetime.now(pytz.timezone('US/Pacific'))

    client = datastore.Client()

    # cannot have multiple filters!?
    groups_query = client.query(
        kind='group',
        filters=[('end_date', '>=', (dt.date() - datetime.timedelta(days=1)).isoformat())],
    )
    subject_prefix = '[DEV] ' if IS_DEVELOPMENT else ''
    for group in groups_query.fetch():
        print(group)
        if dt.date().isoformat() < group['start_date']:
            continue

        final_summary_date = (
            datetime.datetime.strptime(group['end_date'], '%Y-%m-%d').date()
            + datetime.timedelta(days=1)
        ).isoformat()

        is_final = dt.date().isoformat() == final_summary_date
        if not force_send and dt.weekday() != 0 and not is_final and not IS_DEVELOPMENT:
            continue

        goals_query = client.query(
            kind='goal2',
            ancestor=group.key
        )

        goals = list(goals_query.fetch())
        if not goals:
            print('no goals found for group {}'.format(group))
            continue

        personalization = Personalization()
        total_progress = 0
        total_denominator = 0
        for goal in goals:
            print(goal)

            goal['denominator'] = len(goal.get('opportunities', []))
            goal['progress'] = len(goal.get('completions', []))
            goal['background-color'] = compute_goal_color(goal)
            goal['completed_last_week'] = False
            opportunities = goal.get('opportunities', [])
            if opportunities and max(opportunities) in goal.get('completions', []):
                goal['completed_last_week'] = True
            total_progress += goal['progress']
            total_denominator += goal['denominator']

            if IS_DEVELOPMENT and DEVELOPER_EMAIL_STRING not in goal['email']:
                continue
            personalization.add_to(To(email=goal['email']))

        goals = sorted(goals, key=lambda x: x['progress'] / goal['denominator'], reverse=True)
        template = TEMPLATE_ENV.get_template("summary_email.tmpl")
        rendered = template.render(**locals())

        mail = Mail(
            from_email=From(email="eccountabot@gmail.com"),
            subject=Subject(subject_prefix + "Eccountabot {}Summary {} {}".format(
                'Final ' if is_final else '', group['name'], dt.date().isoformat()
            )),
            html_content=Content("text/html", rendered)
        )
        mail.add_personalization(personalization)
        try:
            response = sg.client.mail.send.post(request_body=mail.get())
        except exceptions.BadRequestsError as e:
            print(e.body)
            raise
