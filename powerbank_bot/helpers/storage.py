import logging

import pymongo

from powerbank_bot.config import Mongo

LOGGER = logging.getLogger('Storage')


class Storage:
    def __init__(self):
        self._db = Mongo.get_db()

    def get_dialog_state(self, dialog_id):
        LOGGER.debug('Requested state loading of dialog ({})'.format(dialog_id))
        try:
            return self._db.dialog_state.find_one({'dialog_id': dialog_id})
        except Exception:
            LOGGER.exception('Failed to load state of dialog ({})'.format(dialog_id))

    def upsert_dialog_state(self, dialog_state):
        LOGGER.debug('Requested upsert of dialog ({}) state'.format(dialog_state['dialog_id']))
        try:
            self._db.dialog_state.replace_one({'dialog_id': dialog_state['dialog_id']}, dialog_state, upsert=True)
        except Exception:
            LOGGER.exception('Failed to upsert dialog ({}) state'.format(dialog_state['dialog_id']))
        else:
            LOGGER.exception('Dialog ({}) state upserted successfully'.format(dialog_state['dialog_id']))

    def get_user_request_updates(self, user_id, limit=20):
        try:
            return list(self._db.updates.find({'user_id': user_id, 'seen': False}, limit=limit)
                        .sort('timestamp', pymongo.DESCENDING))
        except:
            LOGGER.exception('Failed to retrieve user ({}) request updates'.format(user_id))

    def mark_request_update_as_seen(self, update_id):
        try:
            self._db.updates.update_one({'update_id': update_id}, {'$set': {'seen': True}}, upsert=False)
        except:
            LOGGER.exception('Failed mark request update ({}) as seen'.format(update_id))
