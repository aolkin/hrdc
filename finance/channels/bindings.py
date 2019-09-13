from channels.binding.websockets import WebsocketBinding

from django.db.models import F

from ..models import *

class BudgetExpenseBinding(WebsocketBinding):
    model = BudgetExpense
    stream = "budgetexpense"
    fields = ("category", "name", "estimate", "reported", "actual", "notes")

    @classmethod
    def group_names(cls, instance):
        return ["budget-show-{}".format(instance.show.pk)]
    
    def has_permission(self, user, action, pk):
        if action == "create":
            return True
        if action == "update" or action == "delete":
            return self.model.objects.get(pk=pk).show.show.user_is_staff(user) or user.is_board
            
    def create(self, data):
        show = FinanceInfo.objects.get(pk=data["show"])
        if show.show.user_is_staff(self.user) or self.user.is_board:
            super().create(data)

    def update(self, pk, data):
        obj = self.model.objects.get(pk=pk)
        if "actual" in data:
            data["actual"] = obj.actual
        if "category" in data:
            data["category"] = obj.category
        super().update(pk, data)
