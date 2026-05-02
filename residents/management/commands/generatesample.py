'''
Generate Resident sectors.
'''


from typing import Any

from django.core.management.base import BaseCommand

from residents.models import ResidentSector


class Command(BaseCommand):
    help = "Generate base Resident sectors."

    base_sectors = [
        {
            "short_name" : "WORKERTEACHER", "name" : "teacher", "description" : None,
        },
        {
            "short_name" : "WORKERHEALTH", "name" : "health worker", "description" : None,
        },
        {
            "short_name" : "WORKERGOV", "name" : "government worker", "description" : None,
        },
        {
            "short_name" : "STUDENT", "name" : "student", "description" : None,
        },
        {
            "short_name" : "SINGLEPARENT", "name" : "single parent", "description" : None,
        },
        {
            "short_name" : "SENIOR", "name" : "senior citizen", "description" : None,
        },
        {
            "short_name" : "SBUSINESSES", "name" : "Small Businesses", "description" : None,
        },
        {
            "short_name" : "RESIDENT", "name" : "resident", "description" : None,
        },
        {
            "short_name" : "PUVJEEP", "name" : "Jeepney Driver", "description" : None,
        },
        {
            "short_name" : "PUVBUS", "name" : "Bus Driver", "description" : None,
        },
        {
            "short_name" : "4PS", "name" : "Pantawid Pamilyang Pilipino Program (4Ps)", "description" : None,
        },
    ]

    def handle(self, *args: Any, **options: Any) -> None :
        for sector in self.base_sectors:
            if ResidentSector.objects.filter(name=sector["name"]).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Sector {sector["name"].title()} already exsits."
                    )
                )
            else:
                try:
                    ResidentSector.objects.create(**sector)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sector {sector["name"].title()} created."
                        )
                    )
                except Exception as err:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Sector {sector["name"].title()} failed to generate: {err}."
                        )
                    )
