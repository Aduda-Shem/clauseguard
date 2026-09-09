import json
from pathlib import Path

from django.core.management.base import BaseCommand

from reviews.models import PlaybookRule

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "fixtures" / "playbook_rules.json"


class Command(BaseCommand):
    help = "Load (or refresh) the playbook rule set from reviews/fixtures/playbook_rules.json"

    def handle(self, *args, **options):
        rules = json.loads(DATA_PATH.read_text())
        created, updated = 0, 0

        for rule in rules:
            _, was_created = PlaybookRule.objects.update_or_create(
                key=rule["key"],
                defaults={
                    "name": rule["name"],
                    "category": rule["category"],
                    "detection_pattern": rule["detection_pattern"],
                    "risk_rules": rule["risk_rules"],
                    "default_risk": rule["default_risk"],
                    "default_reason": rule["default_reason"],
                    "default_redline": rule["default_redline"],
                    "missing_risk": rule["missing_risk"],
                    "missing_reason": rule["missing_reason"],
                    "order": rule["order"],
                    "active": True,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(f"Playbook loaded: {created} created, {updated} updated."))
