import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .handler import handle_dialog


@login_required
def index(request):
    with open('log.log', encoding='utf-8') as log_file:
        data = log_file.readlines()
        context = {'logs': []}
        for line in data:
            if 'INFO' in line and 'Request' in line:
                date, json_txt = line.split(' INFO root Request: ')
                json_dict = eval(json_txt)
                user_id = json_dict['session']['user']['user_id']
                message = ' '.join(json_dict['request']['nlu']['tokens'])
                context['logs'].append(
                    {
                        'user_id': user_id,
                        'message': message,
                        'date': date
                    }
                )
    return render(request, "index.html", context)


logging.basicConfig(
    filename='log.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO
)


@csrf_exempt
def post(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        logging.info(f'Request: {data!r}')
        response = {
            'session': data['session'],
            'version': data['version'],
            'response': {
                'end_session': False
            }
        }
        handle_dialog(data, response)
        logging.info(f'Response:  {response!r}')
        return HttpResponse(json.dumps(response))
    return redirect('index')
