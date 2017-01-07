import calendar
import datetime
import pickle
import uuid

import numpy as np
from flask import Flask, jsonify
from flask import request

from powerbank_bot.config import Mongo, BotApi

bot_api_app = Flask(__name__)


def dt_to_timestamp(dt):
    return calendar.timegm(dt.timetuple())


class ScoringModel:
    def __init__(self, model_path):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def predict_proba(self, x):
        return self.model.predict_proba(x.reshape(1, -1)).ravel()[0]

    def predict_dummy_proba(self, form, use_weights=True):
        schema = [
            ('age', None, [[25, 56], [0.67, 1.0, 0.2]], 1.2),
            ('credit_amount', None, None, 0),
            ('credit_history', 5, [0.8, 1.0, 1.0, 0.33, 0.1], 1.3),
            ('duration_in_month', None, None, 0),
            ('foreign_worker', 'b', [0.83, 0.33], 0.5),
            ('housing', 3, [0.33, 1.0, 0.2], 1),
            ('installment_plans', 3, [0.5, 0.33, 0.5], 0.2),
            ('job', 4, [0.1, 0.33, 0.67, 1.0], 1.1),
            ('other_debtors', 3, [0.2, 0.95, 0.6], 1),
            ('personal_status', 5, [0.5, 0.33, 0.67, 1.0, 0.5], 1.2),
            ('present_employment_since', 5, [0.1, 0.2, 0.5, 0.83, 1.0], 1.3),
            ('property', 4, [1.0, 0.83, 0.83, 0.33], 1.3),
            ('purpose', 11, [0.5] * 11, 0),
            ('status_of_existing_checking_account', 4, [0.33, 0.67, 1.0, 0.5], 1.5),
            ('telephone', 'b', [1.0, 0.33], 0.5)
        ]

        x = 1
        y = 0
        for field_name, conf, classifier, weight in schema:
            if not use_weights:
                weight = 1
            value = form[field_name]
            y += weight
            if conf is None:
                if classifier is None:
                    coef = 0.5
                else:
                    thresholds, weights = classifier
                    coef = weights[len([i for i in thresholds if i < value])]
            else:
                coef = classifier[value]
            x *= (coef ** weight)
        return x ** (1 / y)


def to_feature_vector(form):
    schema = [
        ('age', None),
        ('credit_amount', None),
        ('credit_history', 5),
        ('duration_in_month', None),
        ('foreign_worker', 'b'),
        ('housing', 3),
        ('installment_plans', 3),
        ('job', 4),
        ('other_debtors', 3),
        ('personal_status', 5),
        ('present_employment_since', 5),
        ('property', 4),
        ('purpose', 11),
        ('status_of_existing_checking_account', 4),
        ('telephone', 'b')
    ]

    values = []

    for field_name, conf in schema:
        value = form[field_name]

        if conf in (None, 'b'):
            values.append(value)
        else:
            cat_value = [0] * conf
            cat_value[value] = 1
            values.extend(cat_value)

    return np.array(values)


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


@bot_api_app.route('/predict_proba', methods=['POST', 'GET'])
def predict_proba():
    scoring_form = request.get_json()
    x = to_feature_vector(scoring_form)
    prob = bot_api_app.scoring_model.predict_proba(x)
    dummy_prob = bot_api_app.scoring_model.predict_dummy_proba(scoring_form)
    return jsonify(prob=prob, dummy_prob=dummy_prob)


def run_bot_api():
    scoring_model = ScoringModel(BotApi.scoring_model_path)
    bot_api_app.scoring_model = scoring_model
    bot_api_app.run(BotApi.host, BotApi.port)


if __name__ == '__main__':
    run_bot_api()
