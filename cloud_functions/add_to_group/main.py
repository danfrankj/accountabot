import uuid
import datetime
import pytz
from google.cloud import datastore
from google.cloud.datastore.entity import Entity
from flask import redirect


REQUIRED_KEYS = ['name', 'email', 'description', 'group_id']
BASE_URL = "https://us-central1-accountabot.cloudfunctions.net"

# {
#   "name": "Dan F.",
#   "email":"danfrankj+test@gmail.com",
#   "description": "tesing signup",
#   "group_id": 5715999101812736
# }


def add_to_group(request):
    if request.method == "POST":
        if request.content_type == 'text/plain':
            data = request.get_data()
        elif request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = dict((k, v) for k, v in request.form.items())

    for key in REQUIRED_KEYS:
        if key not in data:
            return '{} is a required'.format(key)

    client = datastore.Client()
    group = client.get(client.key('group', int(data['group_id'])))
    if not group:
        return 'group not found'

    if datetime.datetime.now(pytz.timezone('US/Pacific')).isoformat() >= group['end_date']:
        return 'that goal period has has already ended!'

    query = client.query(kind='goal2', ancestor=group.key, filters=[('email', '=', data['email'])])
    if list(query.fetch()):
        return 'you already have recorded a goal in this group!'

    goal = Entity(client.key('group', group.id, 'goal2', int(uuid.uuid1().int % 1e16)))
    goal['name'] = data['name']
    goal['email'] = data['email']
    goal['description'] = data['description']
    goal['motivation'] = data.get('motivation', None)
    goal['this_week'] = data.get('this_week', None)
    goal['completions'] = []
    goal['opportunities'] = []
    client.put(goal)

    return redirect(
        (BASE_URL + "/view_group?group_id={}").format(group.id),
        code=302
    )
