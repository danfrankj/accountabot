import datetime
import pytz
import jinja2
from google.cloud import datastore

TEMPLATE_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
BASE_URL = "https://us-central1-accountabot.cloudfunctions.net"


def home(request):
    print(request)
    dt = datetime.datetime.now(pytz.timezone('US/Pacific'))

    client = datastore.Client()
    groups = client.query(
        kind='group',
        filters=[('end_date', '>=', dt)],
    ).fetch()
    groups = [group for group in groups if group.get('visible', True)]

    return TEMPLATE_ENV.get_template("home.tmpl").render(**locals())
