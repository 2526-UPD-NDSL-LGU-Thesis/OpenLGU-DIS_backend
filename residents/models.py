"""
Django model for Resident database.
"""

from django.db import models, IntegrityError, transaction

from .generator import generate_id, generate_uid


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


class ResidentSector(models.Model):
    id = models.CharField(max_length=20, editable=False, unique=True, primary_key=True,
                          db_index=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self) -> str:
        return self.short_name if self.short_name else self.name

    def save(self, *args, **kwargs) -> None :
        if not self.id:
            for _ in range(10):
                self.id = "SECTOR" + generate_id(4)
        return super().save(*args, **kwargs)


class Resident(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    pcn = models.CharField(verbose_name="PCN", unique=True, db_index=True)
    uin = models.CharField(unique=True, db_index=True, editable=False)

    sector = models.ManyToManyField(ResidentSector, related_name="sectors")

    issued_at = models.DateField(auto_now_add=True)
    proof_of_residence = models.FileField(upload_to="proofs/")

    active = models.BooleanField(default=True)

    email = models.EmailField(blank=True, null=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    profile_image = models.ImageField(upload_to="profiles/")

    def __str__(self) -> str :
        return str(self.uin)

    def save(self, *args, **kwargs) -> None :
        if not self.uin:
            for _ in range(10):
                self.uin = generate_uid(10)
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.uin = None
            raise ValueError("Failed to generate UIN")
        return super().save(*args, **kwargs)
