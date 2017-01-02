import os
import sys

import pymongo


class Mongo(object):
    db = 'powerbank_bot'

    __hosts = ('ds141368.mlab.com:41368',)

    username = 'bot'
    password = 'bot'
    host = 'mongodb://{}:{}@{}/{}'.format(username, password, ','.join(__hosts), db)

    read_preference = pymongo.ReadPreference.PRIMARY

    connection = {
        'host': host,
        'read_preference': read_preference,
    }

    @classmethod
    def get_db(cls):
        client = pymongo.MongoClient(cls.__hosts)
        db = client.get_database(cls.db)
        db.authenticate(cls.username, cls.password)
        return db


class Api:
    credentials = ('client', 'clientclientclient')
    base_url = 'http://pb.somee.com/api'


class BotApi:
    host = '0.0.0.0'
    port = 5000
    scoring_model_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'model.p')


class Email:
    api_key = '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'
    address = 'bsuir.power.bank@gmail.com'
    sender = 'Power Bank'


class Telegram:
    token = '300227038:AAEqqG_KMPhuq-eydlsT94TMY8eY46WRhjE'
