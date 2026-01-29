# Generated migration file
# Place this in: bulk_orders/migrations/0002_add_reference_field.py

from django.db import migrations, models
import random
import string


def generate_reference():
    """Generate unique reference like JMW-BULK-1234"""
    return f"JMW-BULK-{random.randint(1000, 9999)}"


def populate_existing_references(apps, schema_editor):
    """Populate reference field for existing OrderEntry records"""
    OrderEntry = apps.get_model('bulk_orders', 'OrderEntry')
    
    for order in OrderEntry.objects.filter(reference__isnull=True):
        # Keep generating until we get a unique one
        while True:
            ref = generate_reference()
            if not OrderEntry.objects.filter(reference=ref).exists():
                order.reference = ref
                order.save()
                break


class Migration(migrations.Migration):

    dependencies = [
        ('bulk_orders', '0001_initial'),  # Replace with your last migration
    ]

    operations = [
        # Add reference field (nullable first for existing records)
        migrations.AddField(
            model_name='orderentry',
            name='reference',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        
        # Populate existing records
        migrations.RunPython(populate_existing_references, migrations.RunPython.noop),
        
        # Now make it unique and non-nullable
        migrations.AlterField(
            model_name='orderentry',
            name='reference',
            field=models.CharField(max_length=20, unique=True),
        ),
        
        # Add index for performance
        migrations.AddIndex(
            model_name='orderentry',
            index=models.Index(fields=['reference'], name='order_reference_idx'),
        ),
    ]