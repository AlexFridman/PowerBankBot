import calendar
import datetime
import uuid

from flask import Flask
from flask import request

from powerbank_bot.config import Mongo, BotApi

app = Flask(__name__)


def dt_to_timestamp(dt):
    return calendar.timegm(dt.timetuple())


@app.route('/request_update', methods=['POST'])
def request_update():
    data = request.get_json()
    dt = datetime.datetime.strptime(data['timestamp'][:19], '%Y-%m-%dT%H:%M:%S')

    event = {
        'update_id': str(uuid.uuid4()),
        'request_id': data['request_id'],
        'credit_type_name': data['credit_type_name'],
        'user_id': data['user_id'],
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
        'event_type': event['type']
    },
        event,
        upsert=True
    )
    return 'OK'


if __name__ == '__main__':
    app.run(BotApi.host, BotApi.port)
