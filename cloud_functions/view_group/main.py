import jinja2
from google.cloud import datastore

TEMPLATE_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
BASE_URL = "https://us-central1-accountabot.cloudfunctions.net"


def view_group(request):
    print(request)
    assert request.method == "GET"

    data = dict((k, v) for k, v in request.args.items())
    print(data, 'data')

    if 'group_id' not in data:
        return 'Group id must be included in this request'

    client = datastore.Client()
    group = client.get(client.key('group', int(data['group_id'])))
    if not group:
        return 'group not found'

    goals = client.query(kind='goal2', ancestor=group.key).fetch()
    return TEMPLATE_ENV.get_template("view_group.tmpl").render(**locals())
