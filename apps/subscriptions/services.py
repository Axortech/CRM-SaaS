from datetime import timedelta

from django.utils import timezone

from apps.subscriptions.constants import PLAN_DEFINITIONS
from apps.subscriptions.models import Subscription


def get_plan_definition(plan: str):
    for definition in PLAN_DEFINITIONS:
        if definition["plan"] == plan:
            return definition
    raise ValueError(f"Unknown plan: {plan}")


def calculate_billing_period_end(billing_cycle: str):
    base_date = timezone.now().date()
    duration = 30 if billing_cycle == Subscription.BillingCycle.MONTHLY else 365
    return base_date, base_date + timedelta(days=duration)
