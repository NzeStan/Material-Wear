import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from  . validators import validate_phone_number
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseOrder(models.Model):
    """Base model for all order types"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    serial_number = models.PositiveIntegerField(
        unique=True, editable=False, db_index=True
    )
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=11,
        validators=[validate_phone_number],
        help_text="Enter an 11-digit phone number",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # ✅ NEW: Generation tracking fields
    items_generated = models.BooleanField(
        default=False,
        help_text='Whether order items have been generated/printed'
    )
    generated_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='When the order items were generated'
    )
    generated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='generated_orders',
        help_text='Admin user who generated the order items'
    )

    class Meta:
        ordering = ["-created"]

    def __init__(self, *args, **kwargs):
        user = kwargs.get("user", None)
        super(BaseOrder, self).__init__(*args, **kwargs)
        if user:
            self.email = user.email

    def save(self, *args, **kwargs):
        if not self.serial_number:
            last_serial = BaseOrder.objects.all().order_by("serial_number").last()
            if last_serial:
                self.serial_number = last_serial.serial_number + 1
            else:
                self.serial_number = 1
        super(BaseOrder, self).save(*args, **kwargs)

    def get_full_name(self):
        """Return customer's full name"""
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()

    def get_total_items(self):
        """Return total quantity of items in order"""
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Order #{self.serial_number} - {self.get_full_name()}"


class NyscKitOrder(BaseOrder):
    """NYSC Kit specific order model"""

    call_up_number = models.CharField(
        max_length=20, 
        help_text="NYSC call-up number (e.g., AB/22C/1234)"
   )
    state = models.CharField(max_length=50)
    local_government = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.call_up_number = self.call_up_number.upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "NYSC Kit Order"
        verbose_name_plural = "NYSC Kit Orders"


class NyscTourOrder(BaseOrder):
    """NYSC Tour specific order model"""

    class Meta:
        verbose_name = "NYSC Tour Order"
        verbose_name_plural = "NYSC Tour Orders"


class ChurchOrder(BaseOrder):
    """Church merchandise specific order model"""

    pickup_on_camp = models.BooleanField(default=True)
    delivery_state = models.CharField(max_length=50, blank=True)
    delivery_lga = models.CharField(max_length=100, blank=True)

    def clean(self):
        """Validate delivery details if not picking up on camp"""
        if not self.pickup_on_camp:
            if not self.delivery_state or not self.delivery_lga:
                raise ValidationError(
                    {
                        "delivery_state": "Delivery state is required for non-pickup orders",
                        "delivery_lga": "Delivery LGA is required for non-pickup orders",
                    }
                )

    class Meta:
        verbose_name = "Church Order"
        verbose_name_plural = "Church Orders"


class OrderItem(models.Model):
    order = models.ForeignKey(BaseOrder, related_name="items", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    product = GenericForeignKey("content_type", "object_id")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    quantity = models.PositiveIntegerField(default=1)
    extra_fields = models.JSONField(default=dict, blank=True)

    def get_cost(self):
        return self.price * self.quantity if self.price else 0
