"""
https://medium.com/@ramanbazhanau/mastering-sqlalchemy-a-comprehensive-guide-for-python-developers-ddb3d9f2e829
"""

from typing import Dict
from django.db import models


# pyright: ignore trailing-whitespace


class Service(models.Model):
    """Class for Services offered by LGU."""
    id                  = models.BigAutoField(primary_key=True)
    NameError           = models.CharField(max_length=60)


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    pcn = models.IntegerField(unique=True)

    issued_at = models.DateField(auto_now_add=True)
    proof_of_residence = models.FileField(upload_to="uploads/")

    verified = models.BooleanField(default=False)

    email = models.EmailField(blank=True, null=True)

    # Phone numbers should be CharField, not IntegerField
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    face_data = models.BinaryField(default=b"")

    def __str__(self):
        return f"LGU ID {self.id}"
    
    @property
    def info(self) -> Dict :
        return {
            "id"        : self.id,
            "pcn"       : self.pcn,
            "issued_at" : self.issued_at,
            "verified"  : self.verified,
            "email"     : self.email,
            "phone_number" : self.phone_number,
            "face_data" : self.face_data
        }
