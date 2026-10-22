from hrdc.websockets import DemultiplexConsumer

from .bindings import *


class BudgetConsumer(DemultiplexConsumer):
    bindings = {
        "budgetexpense": BudgetExpenseBinding,
    }

    def has_access(self, **kwargs):
        return (self.user.has_perm("finance.view_budgetexpense") or
                FinanceInfo.objects.get(
                    pk=kwargs["show"]).show.user_is_staff(self.user))

    def connection_groups(self, **kwargs):
        return ["budget-show-{}".format(kwargs["show"])]
