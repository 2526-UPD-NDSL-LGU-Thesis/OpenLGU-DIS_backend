from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from residents.models import User
from .models import Service, ServiceClaim


def claim_service(user : User, service : Service):

    if not service.active:
        raise Exception("Service not active")

    if not user.verified:
        raise Exception("User not verified")

    if not service.max_claims:
        return ServiceClaim.objects.create(user=user, service=service)

    period_start = timezone.now() - timedelta(seconds=service.period_seconds)

    with transaction.atomic():
        recent_claims = ServiceClaim.objects.select_for_update().filter(
            user=user,
            service=service,
            claimed_at__gte=period_start
        )

        if recent_claims.count() >= service.max_claims:
            raise Exception("Claim limit reached")

        return ServiceClaim.objects.create(user=user, service=service)