import requests


class FilePreviews:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = "https://api.filepreviews.io/v2/previews/"

    def generate(self, url, **kwargs):
        payload = {"url": url}

        payload.update(kwargs)

        r = requests.post(
            self._api_url, json=payload, auth=(self.api_key, self.api_secret)
        )

        return r.json()
