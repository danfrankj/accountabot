from google.cloud import datastore


def record_progress(request):
    data = None
    if request.method == "GET":
        data = dict((k, v) for k, v in request.args.items())
    if request.method == "POST":
        if request.content_type == 'text/plain':
            data = request.get_data()
        else:
            data = dict((k, v) for k, v in request.form.items())

    print(data)
    client = datastore.Client()

    goal = client.get(client.key('group', int(data['group_id']), 'goal2', int(data['goal_id'])))
    if not goal:
        raise Exception('goal {} not found'.format(goal))

    if data['opportunity'] not in goal['opportunities']:
        raise Exception('unable to find goal opportunity')

    motivation = data.get('motivation', '')
    if motivation:
        goal['motivation'] = motivation
    this_week = data.get('this_week', '')
    if this_week:
        goal['this_week'] = this_week

    if 'yes_button' in data:
        goal['completions'] = list(set(
            goal.get('completions', []) + [data['opportunity']]
        ))
    client.put(goal)

    if 'no_button' in data:
        return 'We have tomorrows for a reason.'

    new_progress = len(goal['completions'])
    # show a better response! maybe with a cat?
    return 'Yay progress! You have completed {} days. See you next time.'.format(new_progress)
