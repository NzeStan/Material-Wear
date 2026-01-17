from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0002_alter_nysckitorder_call_up_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseorder',
            name='items_generated',
            field=models.BooleanField(default=False, help_text='Whether order items have been generated/printed'),
        ),
        migrations.AddField(
            model_name='baseorder',
            name='generated_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When the order items were generated'),
        ),
        migrations.AddField(
            model_name='baseorder',
            name='generated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='generated_orders',
                to=settings.AUTH_USER_MODEL,
                help_text='Admin user who generated the order items'
            ),
        ),
    ]