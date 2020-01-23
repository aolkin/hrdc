
import hashlib, logging

import requests

from django.conf import settings
from config import config

logger = logging.getLogger(__name__)

def enabled():
    return bool(config.mailchimp_sync_enabled == "yes" and
                config.mailchimp_audience_id)

DOMAIN = "https://{}.api.mailchimp.com".format(
    settings.MAILCHIMP_API_KEY.rpartition("-")[2])

AUTH = ("apikey", settings.MAILCHIMP_API_KEY)

SUBSCRIBED = "subscribed"
UNSUBSCRIBED = "unsubscribed"

class Contact:
    def __init__(self, email):
        self.email = email

    @property
    def url(self):
        return DOMAIN + "/3.0/lists/{}/members/{}".format(
            config.mailchimp_audience_id,
            hashlib.md5(self.email.lower().encode()).hexdigest())

    def get_status(self):
        """
        Possible return values:
        
        - subscribed
        - unsubscribed
        - cleaned
        - pending
        - transactional
        - archived

        - missing (will be returned on 404)
        - error (will be returned otherwise)
        """
        res = requests.get(self.url, auth=AUTH, params={
            "fields": "status"
        })
        if res.status_code == 200:
            return res.json()["status"]
        elif res.status_code == 404:
            return "missing"
        else:
            return "error"

    def update_status(self, status):
        if status not in (SUBSCRIBED, UNSUBSCRIBED):
            raise TypeError("Invalid status")
        res = requests.patch(self.url, auth=AUTH, json={
            "status": status
        })
        if res.status_code != 200:
            logger.error("Failed to set subscription status for '{}' to '{}' ({})".format(self.email, status, res.text))
        return res.status_code == 200

    def create(self, merge_fields):
        res = requests.post(DOMAIN + "/3.0/lists/{}/members/".format(
            config.mailchimp_audience_id), auth=AUTH, params={
                "skip_merge_validation": True,
            }, json={
                "email_address": self.email,
                "email_type": "html",
                "status": SUBSCRIBED,
                "merge_fields": merge_fields,
            })
        if res.status_code != 200:
            logger.error("Failed to add '{}' to the list. ({})".format(self.email, res.text))
        return res.status_code == 200
                      
