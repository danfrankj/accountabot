import os
import datetime
import pytz
import jinja2
import sendgrid
from sendgrid.helpers.mail import Content, Mail, To, Subject, From
from google.cloud import datastore
from python_http_client import exceptions


TEMPLATE_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
IS_DEVELOPMENT = os.environ.get('ACCOUNTABOT_ENVIRONMENT', 'prod').lower() == 'development'
DEVELOPER_EMAIL_STRING = 'danfrankj'


def compute_streak(goal):
    streak = 0
    for opportunity in sorted(goal.get('opportunities', []), reverse=True):
        if opportunity in goal.get('completions', []):
            streak += 1
        else:
            break
    return streak


def compute_group_progress_since_my_last_completion(my_goal, group_goals):
    my_completions = my_goal.get('completions', [])
    my_latest_completion = None
    if my_completions:
        my_latest_completion = max(my_completions)
    group_progress = 0
    for goal in group_goals:
        if goal == my_goal:
            continue
        for completion in goal.get('completions', []):
            if my_latest_completion is None or completion >= my_latest_completion:
                group_progress += 1
    return group_progress


def send_tracking_email(data, context):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
    dt = datetime.datetime.now(pytz.timezone('US/Pacific'))
    print(data, context, dt)

    client = datastore.Client()

    groups_query = client.query(
        kind='group',
        filters=[('end_date', '>=', dt.date().isoformat())],  # cannot have multiple filters!?
    )

    for group in groups_query.fetch():
        print(group)
        if dt.date().isoformat() < group['start_date']:
            continue

        tracking_cadence = group['tracking_cadence']
        if tracking_cadence == 'weekly' and dt.weekday() != 6 and not IS_DEVELOPMENT:  # sunday
            continue

        days_remaining = (
            datetime.datetime.strptime(group['end_date'], '%Y-%m-%d').date() - dt.date()
        ).days
        goals_query = client.query(
            kind='goal2',
            ancestor=group.key
        )

        goals = list(goals_query.fetch())
        if not goals:
            print('no goals found for group {}'.format(group))
            continue
        for goal in goals:
            print(goal)

            streak = compute_streak(goal)
            group_progress_since_my_last_completion = (
                compute_group_progress_since_my_last_completion(goal, goals)
            )
            progress = len(goal.get('completions', []))
            denominator = len(goal.get('opportunities', []))
            opportunity = dt.date().isoformat()
            rendered = TEMPLATE_ENV.get_template("tracking_email.tmpl").render(**locals())

            subject_prefix = '[DEV] ' if IS_DEVELOPMENT else ''
            if IS_DEVELOPMENT and DEVELOPER_EMAIL_STRING not in goal['email']:
                continue

            mail = Mail(
                from_email=From(email="eccountabot@gmail.com"),
                subject=Subject(
                    subject_prefix
                    + "Eccountabot {} {} ".format(group['name'], dt.date().isoformat())
                    + '🔥' * min(int(streak / 3), 5)
                ),
                to_emails=To(email=goal['email']),
                html_content=Content("text/html", rendered)
            )
            try:
                response = sg.client.mail.send.post(request_body=mail.get())
            except exceptions.BadRequestsError as e:
                print(e.body)
                raise

            if tracking_cadence == 'weekly':
                goal['last_week'] = goal.get('this_week', '')
                goal['this_week'] = ''
            goal['opportunities'] = list(set(
                goal.get('opportunities', []) + [opportunity]
            ))

        client.put_multi(goals)
