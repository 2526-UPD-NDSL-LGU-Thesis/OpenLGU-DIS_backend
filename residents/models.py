"""
Django model for Resident database.
"""

from django.db import models, IntegrityError, transaction
from django.conf import settings
import uuid
import os


from .generator import generate_id, generate_uid


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


def image_upload_to(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("profiles/", new_filename)


def proof_upload_to(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("proofs/", new_filename)


class Sector(models.Model):
    id = models.CharField(max_length=20, editable=False, unique=True, primary_key=True,
                          db_index=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None :
        if not self.id:
            for _ in range(10):
                self.id = "SECTOR" + generate_id(4)
        return super().save(*args, **kwargs)


class Resident(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    pcn = models.CharField(verbose_name="PCN", unique=True, db_index=True)
    uin = models.CharField(unique=True, db_index=True, editable=False)

    sector = models.ManyToManyField(Sector, related_name="sectors")

    issued_at = models.DateField(auto_now_add=True)
    proof_of_residence = models.FileField(upload_to=proof_upload_to, blank=True, null=True)

    active = models.BooleanField(default=True)

    email = models.EmailField(blank=True, null=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    profile_image = models.ImageField(upload_to=image_upload_to, blank=True, null=True)

    def __str__(self) -> str :
        return str(self.uin)

    def save(self, *args, **kwargs) -> None :
        if not self.uin:
            for _ in range(10):
                self.uin = generate_uid(settings.UIN_LENGTH)
                try:
                    with transaction.atomic():
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    self.uin = None
            raise ValueError("Failed to generate UIN")
        return super().save(*args, **kwargs)
