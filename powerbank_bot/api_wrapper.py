class ApiWrapper:
    def __init__(self):
        self._authorise()

    def _authorise(self):
        pass

    def get_user_by_phone_number(self, phone_number):
        return True

    def get_user_requests(self, user_id):
        pass

    def get_user_credits(self, user_id):
        pass

    def get_credits(self):
        return [
            {'name': '1', '%': 20},
            {'name': '2', '%': 30},
            {'name': '3', '%': 20},
            {'name': '4', '%': 30},
            {'name': '5', '%': 20},
            {'name': '6', '%': 30},
        ]
