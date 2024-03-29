import logging

import pymongo

from powerbank_bot.helpers.models import RequestUpdate, ScoringForm
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
            return [RequestUpdate.from_json(update) for update in
                    self._db.updates.find({'user_id': user_id, 'seen': False}, limit=limit)
                        .sort('timestamp', pymongo.ASCENDING)]
        except:
            LOGGER.exception('Failed to retrieve user ({}) request updates'.format(user_id))

    def mark_request_update_as_seen(self, update_id):
        try:
            self._db.updates.update_one({'update_id': update_id}, {'$set': {'seen': True}}, upsert=False)
        except:
            LOGGER.exception('Failed mark request update ({}) as seen'.format(update_id))

    def get_scoring_form(self, request_id):
        try:
            form = self._db.scoring_forms.find_one({'request_id': request_id})
            if form:
                return ScoringForm(form)
        except:
            LOGGER.exception('Failed get scoring form ({})'.format(request_id))

    def update_scoring_form(self, form):
        try:
            form = self._db.scoring_forms.replace_one({'request_id': form['request_id']}, form, upsert=True)
        except:
            LOGGER.exception('Failed update scoring form ({})'.format(form['request_id']))
