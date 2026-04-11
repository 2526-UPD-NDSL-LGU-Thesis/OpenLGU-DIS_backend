from django.db import models
from django.utils import timezone
from datetime import timedelta
from residents.models import User
from .generator import generate_id


class Service(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Claim rule
    max_claims = models.IntegerField(null=True, blank=True)
    period_seconds = models.IntegerField(null=True, blank=True)

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def remaining_claims(self, user):
        if not self.max_claims or not self.period_seconds:
            return None  # unlimited

        period_start = timezone.now() - timedelta(seconds=self.period_seconds)

        count = self.claims.filter(
            user=user,
            claimed_at__gte=period_start
        ).count()

        return max(self.max_claims - count, 0)


class ServiceClaim(models.Model):
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(unique=True, db_index=True, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="service_claims"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="claims"
    )

    claimed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["user", "service", "claimed_at"]),
        ]
        ordering = ["-claimed_at"]

    def __str__(self):
        return str(self.transaction_id)
    
    def save(self, *args, **kwargs) -> None :
        if not self.transaction_id:
            for _ in range(10):
                self.transaction_id = generate_id(length=20)
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.transaction_id = None
            raise ValueError("Failed to Transaction ID")
        return super().save(*args, **kwargs)
