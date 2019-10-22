from channels.generic.websockets import (JsonWebsocketConsumer,
                                         WebsocketDemultiplexer)

from .bindings import *

from django.utils import timezone


class BudgetConsumer(WebsocketDemultiplexer):
    http_user = True

    consumers = {
        "budgetexpense": BudgetExpenseBinding.consumer,
    }

    def connect(self, message, **kwargs):
        if not (message.user.has_perm("finance.view_budgetexpense") or
                FinanceInfo.objects.get(
                    pk=kwargs["show"]).show.user_is_staff(message.user)):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)
    
    def connection_groups(self, **kwargs):
        return ["budget-show-{}".format(kwargs["show"])]
