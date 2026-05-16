'''
Generate sample resident data for testing and demonstration purposes.
'''

from pathlib import Path
from typing import Any
from random import sample, randint
import secrets
import string

from django.db import IntegrityError
from django.core.files import File
from django.core.management.base import BaseCommand

from residents.models import Resident, Sector

POR_FILE = Path(r"./residents/sample/proof.pdf")
IMG_FILE = Path(r"./residents/sample/proof.pdf")

SAMPLE_RESIDENTS = 50
SAMPLE_SECTORS = [
    "Resident", "Senior Citizen", "Merchant", "Student", "4Ps", "Single Parent", "PWD", "Farmer",
    "OFW", "LGBTQIA+", "Jeepney Driver"
]
MAX_RETRIES = 10

def generate_id(length : int = 10) -> str :
    """Cryptographically generate a random UID."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

class Command(BaseCommand):
    help = "Generate resident sample data for testing and demonstration purposes."

    def handle(self, *args: Any, **options: Any) -> None :
        # Create Residents
        with open(POR_FILE, "rb") as proof, \
            open(IMG_FILE, "rb") as image:
            
            count = 0
            for _ in range(SAMPLE_RESIDENTS):
                for _ in range(MAX_RETRIES):
                    try:
                        Resident.objects.create(
                            pcn=generate_id(length=10),
                            proof_of_residence=File(proof),
                            profile_image=File(image)
                        )

                        count += 1
                        break
                    except IntegrityError:
                        continue
            
        self.stdout.write(
            self.style.SUCCESS(
                f"Registered {count} sample residents."
            )
        )
        
        # Create sectors
        for sector in SAMPLE_SECTORS:
            if not Sector.objects.filter(name=sector).exists():
                Sector.objects.create(
                    name=sector
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Sector {sector} already exists."
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Registered {len(Sector.objects.all())} sample sectors."
            )
        )
        
        # Assign Residents to Sectors
        residents = Resident.objects.all()
        sector_resident = Sector.objects.filter(name="Resident").first()
        sectors = [s for s in list(Sector.objects.all()) if s != sector_resident]

        for resident in residents:
            assigned = []

            if sector_resident and randint(0, 1):
                assigned.append(sector_resident)
            
            if sectors:
                assigned.extend(
                    sample(sectors, k=min(2, len(sectors)))
                )
            
            resident.sector.add(*assigned)

        self.stdout.write(
            self.style.SUCCESS(
                "Assigned sectors to resident."
            )
        )
