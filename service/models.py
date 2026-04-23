from typing import Tuple, Dict

from django.db import transaction
from django.db import models, IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.utils import timezone
from residents.models import Resident

from .generator import generate_id


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


class Service(models.Model):
    class TypeChoices(models.TextChoices):
        ONCE = "once", "Once"
        PERIODIC = "periodic", "Periodic"
    
    class IntervalChoices(models.TextChoices):
        PERIODIC  = "periodic", "Periodic"
        DAILY     = "daily", "Daily"
        WEEKLY    = "weekly", "Weekly"
        MONTHLY   = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        CUSTOM    = "custom", "Custom"

    name = models.CharField(max_length=40, primary_key=True)
    verbose_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    max_claims_per_user = models.PositiveIntegerField(default=1)

    claim_type = models.CharField(max_length=20, choices=TypeChoices, null=True, blank=True)

    claim_interval = models.CharField(max_length=20, choices=IntervalChoices, null=True, blank=True)

    recepient_sectors = models.ManyToManyField("residents.ResidentSector")

    stocks = models.PositiveIntegerField()

    allowed_groups = models.ManyToManyField(Group, blank=True)

    active = models.BooleanField(default=True)

    def __str__(self) -> str :
        return str(self.name)
    
    def save(self, *args, **kwargs) -> None :
        if self.name:
            self.name = self.name.upper()
        return super().save(*args, **kwargs)
    
    def clean(self) -> None:
        #TODO: Implement Validations
        if self.name:
            self.name = self.name.upper()
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

    claimed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name="claims_made")
    
    notes = models.CharField(blank=True, null=True)

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
    def can_claim(user : Resident, service : Service, amount : int) -> Tuple[bool, Dict] :
        if not service in user.registered_services.all():
            return False, { "error" : "user not registered in services" }
        
        total_claims = ServiceClaim.objects.filter(user=user, service=service).count()
        if total_claims >= service.max_claims_per_user:
            return False, { "error" : "Reached max claims" }

        if int(service.stocks) - amount < 0:
            return False, { "error" : "not enough stocks" }

        return True, { "error" : None }


@transaction.atomic
def claim(user : Resident, service : Service, amount : int, claimed_by : User) -> Tuple[bool, Dict] :
    service = (
        Service.objects
        .select_for_update()
        .get(pk=service.pk)
    )

    res, err = ServiceClaim.can_claim(user, service, amount)

    if not res:
        return False, err
    
    service.stocks -= 1
    service.save(update_fields=["stocks"])

    ServiceClaim.objects.create(
        user=user,
        service=service,
        claimed_by=claimed_by
    )

    return True, { "error": None }
