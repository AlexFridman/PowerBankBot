import pymongo


class Mongo(object):
    db = 'powerbank_bot'

    __hosts = ('ds141368.mlab.com:41368',)

    username = 'b2b'
    password = 'b2b'
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
