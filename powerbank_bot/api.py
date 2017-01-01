from flask import Flask
from flask import request

from powerbank_bot.config import Mongo

app = Flask(__name__)


@app.route('/update', methods=['POST'])
def update():
    event = {
        'user_id': request.form['user_id'],
        'timestamp': request.form['timestamp'],
        'type': request.form['type'],
        'value': request.form['value']
    }

    db = Mongo.get_db()
    updates_collection = db.updates

    updates_collection.replace_one({
        'user_id': event['user_id'],
        'timestamp': event['timestamp'],
        'type': event['type']
    },
        event,
        upsert=True
    )
    return 'OK'


if __name__ == '__main__':
    app.run()
