from notifier import Notifier
from exceptions import NotifierError
import requests
import json
class Plugin(Notifier):
    def send(self, message):
        if 'api_token' not in self.options.keys():
            raise NotifierError("No api_token detected in config file")
        if 'chat_id' not in self.options.keys():
            raise NotifierError("No chat_id detected in config file")
        api_token = self.options['api_token']
        chat_id = self.options['chat_id']
        message = '\n'.join(message)
        url = f"https://api.telegram.org/bot{api_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.get(url,params=params)
        if response.status_code != 200:
            raise NotifierError(f"Server returned: {json.loads(response.text)['description']}")