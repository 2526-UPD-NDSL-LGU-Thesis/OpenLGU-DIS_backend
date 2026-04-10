"""
Django model for Resident database.
"""

from django.db import models, IntegrityError, transaction

from .generator import generate_uid

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    pcn = models.CharField(verbose_name="PCN", unique=True, db_index=True)
    uin = models.CharField(unique=True, db_index=True, editable=False)

    issued_at = models.DateField(auto_now_add=True)
    proof_of_residence = models.FileField(upload_to="proofs/")

    active = models.BooleanField(default=True)

    email = models.EmailField(blank=True, null=True)

    # Phone numbers should be CharField, not IntegerField
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    profile_image = models.ImageField(upload_to="profiles/")

    def __str__(self):
        return f"LGU ID {self.id}"

    def save(self, *args, **kwargs) -> None:
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
