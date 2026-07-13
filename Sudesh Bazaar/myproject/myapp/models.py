from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    image = models.ImageField(upload_to="products/")
    stock = models.PositiveIntegerField(default=0)
    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            discount = (
                (self.original_price - self.price)
                / self.original_price
            ) * 100

            return round(discount)

        return 0

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone = models.CharField(max_length=10)

    def __str__(self):
        return self.user.username
    
class Cart(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} Cart"


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )
    saved_for_later = models.BooleanField(
        default=False
    )


    def __str__(self):
        return (
            f"{self.product.name} "
            f"x {self.quantity}"
        )

    @property
    def total_price(self):
        return self.product.price * self.quantity
    

# =========================================
# WISHLIST
# =========================================

class Wishlist(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlisted_by"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "user",
                    "product",
                ],
                name="unique_user_wishlist_product"
            )

        ]


    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.product.name}"
        )
# =========================================
# DELIVERY ADDRESS
# =========================================

class Address(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=10
    )

    address_line = models.TextField()

    city = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=6
    )

    is_default = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.full_name} - "
            f"{self.city}"
        )


 # =========================================
# ORDER
# =========================================

class Order(models.Model):

    # =====================================
    # ORDER STATUS CHOICES
    # =====================================

    STATUS_CHOICES = [

        ("Placed", "Placed"),

        ("Confirmed", "Confirmed"),

        ("Shipped", "Shipped"),

        (
            "Out for Delivery",
            "Out for Delivery"
        ),

        ("Delivered", "Delivered"),

        ("Cancelled", "Cancelled"),

    ]


    # =====================================
    # CANCEL REASON CHOICES
    # =====================================

    CANCEL_REASON_CHOICES = [

        (
            "Changed my mind",
            "Changed my mind"
        ),

        (
            "Ordered by mistake",
            "Ordered by mistake"
        ),

        (
            "Found a better price",
            "Found a better price"
        ),

        (
            "Delivery taking too long",
            "Delivery taking too long"
        ),

        (
            "Want to change address",
            "Want to change address"
        ),

        (
            "Other",
            "Other"
        ),

    ]


    # =====================================
    # PAYMENT METHOD CHOICES
    # =====================================

    PAYMENT_METHOD_CHOICES = [

        (
            "COD",
            "Cash on Delivery"
        ),

        (
            "ONLINE",
            "Online Payment"
        ),

    ]


    # =====================================
    # PAYMENT STATUS CHOICES
    # =====================================

    PAYMENT_STATUS_CHOICES = [

        (
            "Pending",
            "Pending"
        ),

        (
            "Paid",
            "Paid"
        ),

        (
            "Failed",
            "Failed"
        ),

        (
            "Refunded",
            "Refunded"
        ),

    ]


    # =====================================
    # USER
    # =====================================

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )


    # =====================================
    # DELIVERY ADDRESS
    # =====================================

    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="orders"
    )


    # =====================================
    # ORDER TOTAL
    # =====================================

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )


    # =====================================
    # ORDER STATUS
    # =====================================

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="Placed"
    )


    # =====================================
    # PAYMENT METHOD
    # =====================================

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default="COD"
    )


    # =====================================
    # PAYMENT STATUS
    # =====================================

    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )


    # =====================================
    # RAZORPAY ORDER ID
    # =====================================

    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    # =====================================
    # RAZORPAY PAYMENT ID
    # =====================================

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )


    # =====================================
    # RAZORPAY SIGNATURE
    # =====================================

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )


    # =====================================
    # CANCEL DETAILS
    # =====================================

    cancel_reason = models.CharField(
        max_length=100,
        choices=CANCEL_REASON_CHOICES,
        blank=True,
        null=True
    )


    cancel_note = models.TextField(
        blank=True,
        null=True
    )


    cancelled_at = models.DateTimeField(
        blank=True,
        null=True
    )


    # =====================================
    # CREATED / UPDATED TIME
    # =====================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    # =====================================
    # STRING REPRESENTATION
    # =====================================

    def __str__(self):

        return (
            f"Order #{self.id} - "
            f"{self.user.username}"
        )


    # =====================================
    # CAN CANCEL ORDER
    # =====================================

    @property
    def can_cancel(self):

        return self.status in [

            "Placed",

            "Confirmed",

        ]


    # =====================================
    # ORDER STATUS STEP
    # =====================================

    @property
    def status_step(self):

        status_steps = {

            "Placed": 1,

            "Confirmed": 2,

            "Shipped": 3,

            "Out for Delivery": 4,

            "Delivered": 5,

        }


        return status_steps.get(
            self.status,
            0
        )
    
    @property
    def expected_delivery(self):
        return self.created_at + timedelta(days=3)


# =========================================
# ORDER ITEM
# =========================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )


    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items"
    )


    product_name = models.CharField(
        max_length=200
    )


    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    quantity = models.PositiveIntegerField(
        default=1
    )


    def __str__(self):

        return (
            f"{self.product_name} "
            f"x {self.quantity}"
        )


    @property
    def total_price(self):

        return (
            self.price
            * self.quantity
        )
    
# =========================================
# PRODUCT REVIEW
# =========================================

class ProductReview(models.Model):

    RATING_CHOICES = [

        (1, "1 Star"),

        (2, "2 Stars"),

        (3, "3 Stars"),

        (4, "4 Stars"),

        (5, "5 Stars"),

    ]


    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )


    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="product_reviews"
    )


    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES
    )


    review = models.TextField(
        max_length=1000
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "product",
                    "user",
                ],
                name="unique_product_user_review"
            )

        ]


        ordering = [
            "-created_at"
        ]


    def __str__(self):

        return (
            f"{self.product.name} - "
            f"{self.user.username} - "
            f"{self.rating} Star"
        )