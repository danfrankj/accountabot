import uuid
from google.cloud import datastore
from google.cloud.datastore.entity import Entity
from flask import redirect


REQUIRED_KEYS = ['name', 'start_date', 'end_date', 'tracking_cadence']  # , 'summary_cadence']
BASE_URL = "https://us-central1-accountabot.cloudfunctions.net"
# {
#     "name": "test_group",
#     "start_date": "2019-01-21",
#     "end_date": "2019-01-23",
#     "tracking_cadence": "daily",
#     "summary_cadence": "weekly"
# }


def create_group(request):
    data = None
    if request.method == "GET":
        data = dict((k, v) for k, v in request.args.items())
    if request.method == "POST":
        if request.content_type == 'text/plain':
            data = request.get_data()
        elif request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = dict((k, v) for k, v in request.form.items())

    print(request)
    print(data)
    for key in REQUIRED_KEYS:
        if key not in data:
            return '{} is a required'.format(key)

    client = datastore.Client()
    query = client.query(kind='group')
    query.add_filter('name', '=', data['name'])

    if list(query.fetch()):
        return 'goal already exists with this name'

    group = Entity(client.key('group', int(uuid.uuid1().int % 1e16)))
    group['name'] = data['name']
    group['start_date'] = data['start_date']
    group['end_date'] = data['end_date']
    group['tracking_cadence'] = data['tracking_cadence']

    client.put(group)

    return redirect(
        (BASE_URL + "/view_group?group_id={}").format(group.id),
        code=302
    )
