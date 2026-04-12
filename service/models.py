from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User as Official
from django.db import models, IntegrityError, transaction
from django.utils import timezone
from residents.models import User as Resident

from .generator import generate_id


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


class Service(models.Model):
    # class ClaimPolicy(models.TextChoices):
    #     PER_USER = "per_user", "Per User"
    #     SHARED_STOCK = "shared_stock", "Shared Stock"

    # class ClaimTypes(models.TextChoices):
    #     ONCE = "once", "Once"
    #     PERIODIC = "periodic", "Periodic"
    #     COOLDOWN = "cooldown", "Cooldown"

    # class ClaimPeriods(models.TextChoices):
    #     DAILY = "daily", "Daily"
    #     WEEKLY = "weekly", "Weekly"
    #     MONTHLY = "monthly", "Monthly"
    #     QUARTERLY = "quarterly", "Quarterly"
    #     YEARLY = "yearly", "Yearly"
    
    # class ClaimResetDay(models.TextChoices):
    #     SUNDAY = "sunday", "Sunday"
    #     MONDAY = "monday", "Monday"
    #     TEUSDAY = "teusday", "Teusday"
    #     WEDNESDAY = "wednesday", "Wednesday"
    #     THURSDAY = "thursday", "Thursday"
    #     FRIDAY = "friday", "Friday"
    #     SATURDAY = "saturday", "Saturday"
    
    # class InventoryTypes(models.TextChoices):
    #     UNLIMITED = "unlimited", "Unlimited"
    #     LIMITED = "limited", "Limited"

    name = models.CharField(max_length=40, primary_key=True)
    verbose_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    # claim_policy = models.CharField(max_length=20, choices=ClaimPolicy, null=True, blank=True)
    
    # claim_type = models.CharField(max_length=20, choices=ClaimTypes, null=True, blank=True)

    # claim_period = models.CharField(max_length=20, choices=ClaimPeriods, null=True, blank=True)

    # claim_reset_day = models.CharField(max_length=20, choices=ClaimResetDay, null=True, blank=True)

    stocks = models.PositiveIntegerField()

    active = models.BooleanField(default=True)

    def __str__(self) -> str :
        return str(self.name)
    
    def save(self, *args, **kwargs) -> None :
        return super().save(*args, **kwargs)
    
    def clean(self) -> None:
        #TODO: Implement Validations
        return super().clean()


class ServiceClaim(models.Model):
    id = models.BigAutoField(primary_key=True)
    transaction_id = models.CharField(unique=True, db_index=True, editable=False)

    user = models.ForeignKey(
        Resident,
        on_delete=models.CASCADE,
        related_name="service_claims"
    )

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="claims"
    )

    claimed_at = models.DateTimeField(default=timezone.now)

    claimed_by = models.ForeignKey(Official, on_delete=models.SET_NULL, null=True, related_name="claims_made")

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

    @staticmethod
    def can_claim(user : Resident, service : Service, amount : int) -> bool :
        if not service in user.registered_services:
            return False

        if int(service.stocks) - amount < 0:
            return False

        return True


@transaction.atomic
def claim(user : Resident, service : Service, amount : int, claimed_by : Official) -> bool :
    service = (
        Service.objects
        .select_for_update()
        .get(pk=service.pk)
    )

    if not ServiceClaim.can_claim(user, service, amount):
        return False
    
    service.stocks -= 1
    service.save(update_fields=["stocks"])

    ServiceClaim.objects.create(
        user=user,
        service=service,
        claimed_by=claimed_by
    )

    return True


class GiveawayService(ServiceClaim):
    class Meta:
        proxy = True
        verbose_name = "Giveaway Claims"
        verbose_name_plural = "Giveaway Claims"
