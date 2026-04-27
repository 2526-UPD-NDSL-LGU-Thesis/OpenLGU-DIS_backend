from typing import Tuple, Dict

from datetime import timedelta
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
    class StockChoices(models.TextChoices):
        LIMITED = "limited", "Limited"
        UNLIMITED = "unlimited", "Unlimited"

    class ClaimChoices(models.TextChoices):
        ONETIME = "onetime", "One-Time"
        PERIODIC = "periodic", "Periodic"
    
    class IntervalChoices(models.TextChoices):
        DAILY     = "daily", "Daily"
        WEEKLY    = "weekly", "Weekly"
        MONTHLY   = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY    = "yearly", "Yearly"

    name = models.CharField(max_length=40, primary_key=True)
    verbose_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    max_claims_per_user = models.PositiveIntegerField(default=1)

    claim_type = models.CharField(max_length=20, choices=ClaimChoices)

    refresh_interval = models.CharField(max_length=20, choices=IntervalChoices,
                                        null=True, blank=True)

    recepient_sectors = models.ManyToManyField("residents.ResidentSector")

    stocks_type = models.CharField(max_length=20, choices=StockChoices)

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
        if self.name:
            self.name = self.name.upper()

        if self.verbose_name:
            self.verbose_name = self.verbose_name.title()
        
        if self.claim_type == self.ClaimChoices.ONETIME:
            if self.refresh_interval != None:
                raise ValidationError({
                    "refresh_interval" : "Must be `NONE` when claim type is `ONETIME`."
                })
        
        if self.claim_type == self.ClaimChoices.PERIODIC:
            if self.refresh_interval == None:
                raise ValidationError({
                    "refresh_interval" : "Must not be empty when claim type is `PERIODIC`."
                })

        return super().clean()

    def can_claim(self, resident : Resident, official : User, amount : int) -> Tuple[bool, Dict] :
        # Check if User is authorized to make claims on the service.
        if not self.allowed_groups.filter(id__in=official.groups.all()).exists():
            return False, {
                "error"   : "user_unauthorized",
                "details" : "User doing the claim is not authorized to dispense service."
            }

        # Check if service is active.
        if not self.active:
            return False, { 
                "error"   : "service_inactive",
                "details" : "Service is not active."
            }
        
        # Check if resident is a valid recepient of the service.
        if not self.recepient_sectors.filter(name__in=resident.sector.all()).exists():
            return False, {
                "error"   : "resident_not_a_recepient",
                "details" : "Resident is not a recepient of the service."
            }
        
        # Claim Logic
        if self.claim_type == Service.ClaimChoices.ONETIME:
            total_claims = ServiceClaim.objects.filter(user=resident, service=self).count()
            if total_claims + amount > self.max_claims_per_user:
                return False, {
                    "error"   : "service_maxed_out_claims",
                    "details" : "User has reached the maximum amount of claims."
                }
        
        if self.claim_type == Service.ClaimChoices.PERIODIC:
            total_claims = ServiceClaim.objects.filter(user=resident, service=self)
            today = timezone.now()
            periodic_claims = -1
            
            if self.refresh_interval == Service.IntervalChoices.DAILY:
                periodic_claims = total_claims.filter(claimed_at__date=today).count()
            
            if self.refresh_interval == Service.IntervalChoices.WEEKLY:
                start_of_week = today - timedelta(days=today.weekday())
                periodic_claims = total_claims.filter(
                    claimed_at__date__gte=start_of_week.date()
                ).count()
            
            if self.refresh_interval == Service.IntervalChoices.MONTHLY:
                periodic_claims = total_claims.filter(
                    claimed_at__year=today.year,
                    claimed_at__month=today.month
                ).count()
            
            if self.refresh_interval == Service.IntervalChoices.QUARTERLY:
                quarter = (today.month - 1) // 3 + 1
                start_month = 3 * (quarter - 1) + 1
                end_month = start_month + 2

                periodic_claims = total_claims.filter(
                    claimed_at__year=today.year,
                    claimed_at__date__gte=start_month,
                    claimed_at__date__lte=end_month
                )
            
            if self.refresh_interval == Service.IntervalChoices.YEARLY:
                periodic_claims = total_claims.filter(
                    claimed_at__year=today.year
                ).count()

            if periodic_claims == -1:
                return False, {
                    "error"   : "service_unknown_refresh",
                    "details" : "Service refresh interval is not recognized."
                }
            
            if periodic_claims + amount > self.max_claims_per_user:
                return False, {
                    "error"   : "service_maxed_out_claims",
                    "details" : "User has reached the maximum amount of claims."
                }

        if int(self.stocks) - amount < 0:
            return False, { "error" : "not enough stocks" }

        return True, { "error" : None }


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


@transaction.atomic
def claim(resident : Resident, service : Service, amount : int, claimed_by : User) -> Tuple[bool, Dict] :
    service = (
        Service.objects
        .select_for_update()
        .get(name=service.name)
    )

    status, error = service.can_claim(resident, claimed_by, amount)

    if not status:
        return False, error

    try:
        ServiceClaim.objects.create(
            user=resident,
            service=service,
            claimed_by=claimed_by
        )

        if service.stocks_type == Service.StockChoices.LIMITED:
            service.stocks -= amount
            service.save(update_fields=["stocks"])
    except Exception as err:
        return False, { "error" : f"Failed to save service claim: {err}"}

    return True, { "error": None }
