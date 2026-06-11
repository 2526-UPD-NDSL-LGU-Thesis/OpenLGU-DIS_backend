'''
Generate sample service data for testing and demonstration purposes.
'''


from typing import Any
from random import sample, choice, choices, randint

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group as BaseGroup
from django.contrib.auth import get_user_model

from residents.models import Resident, Sector
from service.models import Group, Assignment, Service, Claim

SAMPLE_GROUPS = [
    "Merchants", "Social Welfare", "Service and Outreach Unit", "Service Delivery Team",
    "Public Service", "Community Assitance", "Citizen Support"
]
SAMPLE_USERS = [
    "simonpeter", "andrew", "jamesthegreater", "john", "philip", "bartholomew", "thomas", "matthew",
    "jamestheless", "thaddaeus", "simonthezealot", "judasiscariot", "lanze", "james", "wilson",
    "alfred", "batman", "superman", "spiderman", 
]
SAMPLE_SERVICES = 50


class Command(BaseCommand):
    help = "Generate service sample data for testing and demonstration purposes."

    def handle(self, *args: Any, **options: Any) -> None :
        # Generate Claiming Groups
        for group in SAMPLE_GROUPS:
            if not Group.objects.filter(name=group).exists():
                Group.objects.create(
                    name=group
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Group {group} already exists."
                    )
                )
        groups = Group.objects.all()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(groups)} groups."
            )
        )

        # Generate Services
        sectors = Sector.objects.all()

        for i in range(SAMPLE_SERVICES):
            max_claims_per_user = choice([1, 3, 5])

            claim_type = choice([_choice.value for _choice in Service.ClaimChoices])
            if claim_type == Service.ClaimChoices.PERIODIC:
                refresh_interval = choice([_choice.value for _choice in Service.IntervalChoices])
            else:
                refresh_interval = None

            stocks_type = choice([_choice.value for _choice in Service.StockChoices])
            if stocks_type == Service.StockChoices.LIMITED:
                stocks = choice([100, 200, 300, 500, 1000])
            else:
                stocks = None
            
            recipient_sectors = sample(
                list(sectors), k=randint(1, len(sectors) // 2)
            )

            allowed_groups = sample(
                list(groups), k=randint(1, len(groups) // 2)
            )

            if not Service.objects.filter(name=f"Service_{i}").exists():
                service = Service.objects.create(
                    name=f"Service_{i}",
                    max_claims_per_user=max_claims_per_user,
                    claim_type=claim_type,
                    refresh_interval=refresh_interval,
                    stocks_type=stocks_type,
                    stocks=stocks,
                )

                service.recipient_sectors.add(*recipient_sectors)
                service.allowed_groups.add(*allowed_groups)
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Service {i} already exists."
                    )
                )
        
        services = Service.objects.all()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(services)} services."
            )
        )

        # Generate Users
        User = get_user_model()
        for name in SAMPLE_USERS:
            if not User.objects.filter(username=name).exists():
                User.objects.create_user(
                    username=name,
                    password="rootroot"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"User {name} already exists."
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(User.objects.all())} users."
            )
        )

        # Generate Assignment
        users = User.objects.filter(is_superuser=False)
        service_claim_roles = BaseGroup.objects.filter(name__contains="Service Claim")
        for user in users:
            if not Assignment.objects.filter(user=user).exists():
                user.groups.add(choice(service_claim_roles))

                assignment = Assignment.objects.create(user=user)

                assignment.groups.set(
                    choices(list(groups), k=randint(1, len(groups)))
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Assignment for User {user.username} already exists."
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(Assignment.objects.all())} assignments."
            )
        )

        # Generate Claims
        active_services = Service.objects.filter(active=True)
        residents = Resident.objects.filter(active=True)
        for service in active_services:
            selected_residents = sample(list(residents), k=randint(1, len(residents)))

            for resident in selected_residents:
                official = choice(list(users))
                if service.can_claim(resident, official, 1):
                    service.claim(resident, official, 1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(Claim.objects.all())} claims."
            )
        )
