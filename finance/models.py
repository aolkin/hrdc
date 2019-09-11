from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth import get_user_model

from django.urls import reverse_lazy

from dramaorg.models import Space, Season, Show

class FinanceInfo(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="finance_info")

    class Meta:
        verbose_name = "Finance-Enabled Show"

    def planned_income(self):
        sum = self.income_set.exclude(status=11).aggregate(
            models.Sum("amount_requested"))["amount_requested__sum"]
        return "${:.2f}".format(sum) if sum else sum
        
    def received_income(self):
        sum = self.income_set.filter(status__gt=90).aggregate(
            models.Sum("amount_received"))["amount_received__sum"]
        return "${:.2f}".format(sum) if sum else sum
        
    def __str__(self):
        return str(self.show)

class Income(models.Model):
    INCOME_STATUSES = (
        (0, "Planned"),
        (1, "Applied"),
        (10, "Confirmed"),
        (11, "Rejected"),
        (
            "Administrative Statuses", (
                (91, "Funds Received"),
                (92, "A.R.T. Grant"),
            )
        )
    )
    
    show = models.ForeignKey(FinanceInfo, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)

    amount_requested = models.DecimalField(decimal_places=2, max_digits=7)
    amount_received = models.DecimalField(decimal_places=2, max_digits=7,
                                          null=True, blank=True)

    status = models.PositiveSmallIntegerField(choices=INCOME_STATUSES,
                                              default=0)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Grant/Income"
