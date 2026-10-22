from hrdc.websockets import DemultiplexConsumer

from .bindings import *


class BudgetConsumer(DemultiplexConsumer):
    bindings = {
        "budgetexpense": BudgetExpenseBinding,
    }

    def has_access(self):
        return (self.user.has_perm("finance.view_budgetexpense") or
                FinanceInfo.objects.get(
                    pk=self.url_kwargs["show"]).show.user_is_staff(self.user))

    def connection_groups(self):
        return ["budget-show-{}".format(self.url_kwargs["show"])]
