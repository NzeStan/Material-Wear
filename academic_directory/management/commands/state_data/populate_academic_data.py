# academic_directory/management/commands/populate_academic_data.py
"""
Management command: populate_academic_data

Seeds the database with Nigerian universities, their faculties, and departments.
Safe to run multiple times — uses get_or_create so existing records are untouched.

Usage:
    python manage.py populate_academic_data             # seed everything
    python manage.py populate_academic_data --dry-run   # preview only
    python manage.py populate_academic_data --university UNN  # seed one university
    python manage.py populate_academic_data --university UNILAG --university UNIBEN
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from .state_data import UNIVERSITIES


class Command(BaseCommand):
    help = (
        "Seed the database with Nigerian universities, faculties, and departments.\n"
        "Safe to run multiple times — uses get_or_create so existing records are preserved.\n\n"
        "Examples:\n"
        "  python manage.py populate_academic_data\n"
        "  python manage.py populate_academic_data --dry-run\n"
        "  python manage.py populate_academic_data --university UNN\n"
        "  python manage.py populate_academic_data --university UNILAG --university UNIBEN"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be created without writing to the database.',
        )
        parser.add_argument(
            '--university',
            action='append',
            metavar='ABBREVIATION',
            dest='universities',
            help='Only seed the specified university (by abbreviation). Repeatable.',
        )

    def handle(self, *args, **options):
        from academic_directory.models import University, Faculty, Department

        dry_run = options['dry_run']
        filter_universities = [u.upper() for u in (options.get('universities') or [])]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be saved.\n"))

        data = UNIVERSITIES
        if filter_universities:
            data = [u for u in data if u['abbreviation'] in filter_universities]
            if not data:
                self.stderr.write(
                    self.style.ERROR(
                        f"No matching universities found for: {filter_universities}\n"
                        f"Available: {[u['abbreviation'] for u in UNIVERSITIES]}"
                    )
                )
                return

        total_universities = 0
        total_faculties = 0
        total_departments = 0

        try:
            with transaction.atomic():
                for uni_data in data:
                    uni_label = f"{uni_data['abbreviation']} ({uni_data['name']})"

                    if dry_run:
                        self.stdout.write(f"  [University] {uni_label}")
                    else:
                        uni, uni_created = University.objects.get_or_create(
                            abbreviation=uni_data['abbreviation'],
                            defaults={
                                'name': uni_data['name'],
                                'state': uni_data['state'],
                                'type': uni_data['type'],
                                'is_active': True,
                            },
                        )
                        if uni_created:
                            total_universities += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✅ Created University: {uni_label}")
                            )
                        else:
                            self.stdout.write(f"  ⏩ Skipped (exists): University {uni_label}")

                    for fac_data in uni_data.get('faculties', []):
                        fac_label = f"{fac_data['abbreviation']} — {fac_data['name']}"

                        if dry_run:
                            self.stdout.write(f"    [Faculty] {fac_label}")
                        else:
                            fac, fac_created = Faculty.objects.get_or_create(
                                university=uni,
                                name=fac_data['name'],
                                defaults={
                                    'abbreviation': fac_data['abbreviation'],
                                    'is_active': True,
                                },
                            )
                            if fac_created:
                                total_faculties += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f"    ✅ Created Faculty: {fac_label}")
                                )
                            else:
                                self.stdout.write(f"    ⏩ Skipped (exists): Faculty {fac_label}")

                        for dept_data in fac_data.get('departments', []):
                            dept_label = f"{dept_data['abbreviation']} — {dept_data['name']}"

                            if dry_run:
                                self.stdout.write(f"      [Department] {dept_label}")
                            else:
                                dept, dept_created = Department.objects.get_or_create(
                                    faculty=fac,
                                    name=dept_data['name'],
                                    defaults={
                                        'abbreviation': dept_data['abbreviation'],
                                        'is_active': True,
                                    },
                                )
                                if dept_created:
                                    total_departments += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(f"      ✅ Created Department: {dept_label}")
                                    )
                                else:
                                    self.stdout.write(
                                        f"      ⏩ Skipped (exists): Department {dept_label}"
                                    )

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Error during seeding: {exc}"))
            raise

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Done! Created {total_universities} universities, "
                    f"{total_faculties} faculties, {total_departments} departments."
                )
            )
        else:
            self.stdout.write(self.style.WARNING("\nDRY RUN complete — no changes were saved."))
