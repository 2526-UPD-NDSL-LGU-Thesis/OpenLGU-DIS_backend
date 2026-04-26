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
            "name" : "WORKERTEACHER", "verbose_name" : "teacher", "description" : None,
        },
        {
            "name" : "WORKERHEALTH", "verbose_name" : "health worker", "description" : None,
        },
        {
            "name" : "WORKERGOV", "verbose_name" : "government worker", "description" : None,
        },
        {
            "name" : "STUDENT", "verbose_name" : "student", "description" : None,
        },
        {
            "name" : "SINGLEPARENT", "verbose_name" : "single parent", "description" : None,
        },
        {
            "name" : "SENIOR", "verbose_name" : "senior citizen", "description" : None,
        },
        {
            "name" : "SBUSINESSES", "verbose_name" : "Small Businesses", "description" : None,
        },
        {
            "name" : "RESIDENT", "verbose_name" : "resident", "description" : None,
        },
        {
            "name" : "PUVJEEP", "verbose_name" : "Jeepney Driver", "description" : None,
        },
        {
            "name" : "PUVBUS", "verbose_name" : "Bus Driver", "description" : None,
        },
        {
            "name" : "4PS", "verbose_name" : "Pantawid Pamilyang Pilipino Program (4Ps)", "description" : None,
        },
    ]

    def handle(self, *args: Any, **options: Any) -> None :
        for sector in self.base_sectors:
            if ResidentSector.objects.filter(name=sector["name"]).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Sector {sector["name"]} already exsits."
                    )
                )
            else:
                try:
                    ResidentSector.objects.create(**sector)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sector {sector["name"]} created."
                        )
                    )
                except Exception as err:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Sector {sector["name"]} failed to generate: {err}."
                        )
                    )