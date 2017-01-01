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
