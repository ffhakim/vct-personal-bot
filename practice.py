import requests
from config import WEBHOOK_URL

requests.post(WEBHOOK_URL, json={"content": "Hello again, now from a safe place!"})