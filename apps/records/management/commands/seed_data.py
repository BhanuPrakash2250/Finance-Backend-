"""
Management command: seed_data

Creates sample users and financial records for development/testing.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear   # wipe existing data first
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random
from decimal import Decimal

from apps.users.models import User
from apps.records.models import FinancialRecord


SAMPLE_USERS = [
    {
        'email': 'admin@finance.com',
        'password': 'Admin@123',
        'first_name': 'Alice',
        'last_name': 'Administrator',
        'role': 'admin',
    },
    {
        'email': 'analyst@finance.com',
        'password': 'Analyst@123',
        'first_name': 'Bob',
        'last_name': 'Analytics',
        'role': 'analyst',
    },
    {
        'email': 'viewer@finance.com',
        'password': 'Viewer@123',
        'first_name': 'Carol',
        'last_name': 'Viewer',
        'role': 'viewer',
    },
]

INCOME_RECORDS = [
    {'amount': Decimal('5000.00'), 'category': 'salary',    'notes': 'Monthly salary – January'},
    {'amount': Decimal('5000.00'), 'category': 'salary',    'notes': 'Monthly salary – February'},
    {'amount': Decimal('5000.00'), 'category': 'salary',    'notes': 'Monthly salary – March'},
    {'amount': Decimal('1200.00'), 'category': 'freelance', 'notes': 'Web design project'},
    {'amount': Decimal('800.00'),  'category': 'freelance', 'notes': 'Logo design project'},
    {'amount': Decimal('450.00'),  'category': 'investment','notes': 'Dividend payout – Q1'},
    {'amount': Decimal('300.00'),  'category': 'investment','notes': 'Stock sale profit'},
]

EXPENSE_RECORDS = [
    {'amount': Decimal('1200.00'), 'category': 'rent',       'notes': 'Monthly apartment rent'},
    {'amount': Decimal('85.00'),   'category': 'utilities',  'notes': 'Electricity bill'},
    {'amount': Decimal('50.00'),   'category': 'utilities',  'notes': 'Internet subscription'},
    {'amount': Decimal('340.00'),  'category': 'groceries',  'notes': 'Weekly grocery shopping'},
    {'amount': Decimal('120.00'),  'category': 'transport',  'notes': 'Monthly metro pass'},
    {'amount': Decimal('65.00'),   'category': 'dining',     'notes': 'Team lunch outing'},
    {'amount': Decimal('200.00'),  'category': 'shopping',   'notes': 'New shoes and clothes'},
    {'amount': Decimal('150.00'),  'category': 'healthcare', 'notes': 'Dentist appointment'},
    {'amount': Decimal('40.00'),   'category': 'education',  'notes': 'Online Python course'},
    {'amount': Decimal('890.00'),  'category': 'travel',     'notes': 'Weekend trip flights'},
]


class Command(BaseCommand):
    help = 'Seeds the database with sample users and financial records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            FinancialRecord.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # ── Create Users ──────────────────────────────────────────────────────
        self.stdout.write('\nCreating users...')
        created_users = {}
        for u in SAMPLE_USERS:
            user, created = User.objects.get_or_create(
                email=u['email'],
                defaults={
                    'first_name': u['first_name'],
                    'last_name':  u['last_name'],
                    'role':       u['role'],
                }
            )
            if created:
                user.set_password(u['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {u["role"]}: {u["email"]}'))
            else:
                self.stdout.write(f'  ~ Already exists: {u["email"]}')
            created_users[u['role']] = user

        admin_user = created_users.get('admin')

        # ── Create Financial Records ──────────────────────────────────────────
        self.stdout.write('\nCreating financial records...')
        today = date.today()

        for i, record_data in enumerate(INCOME_RECORDS):
            # Spread records over the past 3 months
            record_date = today - timedelta(days=random.randint(0, 90))
            FinancialRecord.objects.create(
                type='income',
                date=record_date,
                created_by=admin_user,
                **record_data
            )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(INCOME_RECORDS)} income records'))

        for i, record_data in enumerate(EXPENSE_RECORDS):
            record_date = today - timedelta(days=random.randint(0, 90))
            FinancialRecord.objects.create(
                type='expense',
                date=record_date,
                created_by=admin_user,
                **record_data
            )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(EXPENSE_RECORDS)} expense records'))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Seed completed!\n'))
        self.stdout.write('Test Credentials:')
        for u in SAMPLE_USERS:
            self.stdout.write(f'  {u["role"].upper():8} | {u["email"]:30} | {u["password"]}')
        self.stdout.write('')
