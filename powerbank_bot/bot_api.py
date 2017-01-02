import calendar
import datetime
import uuid

from flask import Flask, jsonify
from flask import request

from powerbank_bot.config import Mongo, BotApi

bot_api_app = Flask(__name__)


def dt_to_timestamp(dt):
    return calendar.timegm(dt.timetuple())


@bot_api_app.route('/request_update', methods=['POST'])
def request_update():
    data = request.get_json()
    dt = datetime.datetime.strptime(data['timestamp'][:19], '%Y-%m-%dT%H:%M:%S')

    event = {
        'update_id': str(uuid.uuid4()),
        'request_id': data['request_id'],
        'credit_type_name': data['credit_type_name'],
        'user_id': str(data['user_id']),
        'timestamp': dt_to_timestamp(dt),
        'event_type': data['type'],
        'event_value': data['value'],
        'seen': False
    }

    db = Mongo.get_db()
    updates_collection = db.updates

    updates_collection.replace_one({
        'user_id': event['user_id'],
        'request_id': event['request_id'],
        'timestamp': event['timestamp'],
        'event_type': event['event_type']
    },
        event,
        upsert=True
    )
    return 'OK'


@bot_api_app.route('/predict_proba')
def predict_proba():
    scoring_form = request.get_json()
    prob = 0.8
    return jsonify(prob=prob)


if __name__ == '__main__':
    bot_api_app.run(BotApi.host, BotApi.port)
