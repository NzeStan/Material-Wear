# Generated migration for excel_bulk_orders
# Run with: python manage.py migrate excel_bulk_orders

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('excel_bulk_orders', '0001_initial'),  # Adjust this to your last migration
    ]

    operations = [
        migrations.CreateModel(
            name='ExcelCouponCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=50, unique=True)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bulk_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupons', to='excel_bulk_orders.excelbulkorder')),
            ],
            options={
                'verbose_name': 'Excel Coupon Code',
                'verbose_name_plural': 'Excel Coupon Codes',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='excelcouponcode',
            index=models.Index(fields=['bulk_order', 'is_used'], name='excel_coupon_bulk_used_idx'),
        ),
        migrations.AddIndex(
            model_name='excelcouponcode',
            index=models.Index(fields=['code'], name='excel_coupon_code_idx'),
        ),
        # Update ExcelParticipant coupon FK to point to ExcelCouponCode
        migrations.AlterField(
            model_name='excelparticipant',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='participants', to='excel_bulk_orders.excelcouponcode'),
        ),
    ]