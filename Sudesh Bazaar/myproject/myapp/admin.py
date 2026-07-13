from django.contrib import admin

from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Product,
    Category,
    Profile,
    Cart,
    CartItem,
    Address,
    Order,
    OrderItem,
)


# =========================================
# CATEGORY
# =========================================

@admin.register(Category)
class CategoryAdmin(ModelAdmin):

    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )


# =========================================
# PRODUCT
# =========================================

@admin.register(Product)
class ProductAdmin(ModelAdmin):

    list_display = (
        "id",
        "name",
        "category",
        "price",
        "original_price",
        "stock",
    )

    # PRODUCT ID + NAME CLICKABLE
    list_display_links = (
        "id",
        "name",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "name",
        "category__name",
    )

    ordering = (
        "-id",
    )

    list_per_page = 20

# =========================================
# PROFILE
# =========================================

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):

    list_display = (
        "id",
        "user",
        "phone",
    )

    search_fields = (
        "user__username",
        "user__email",
        "phone",
    )


# =========================================
# CART
# =========================================

@admin.register(Cart)
class CartAdmin(ModelAdmin):

    list_display = (
        "id",
        "user",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
    )


# =========================================
# CART ITEM
# =========================================

@admin.register(CartItem)
class CartItemAdmin(ModelAdmin):

    list_display = (
        "id",
        "cart",
        "product",
        "quantity",
        "saved_for_later",
    )

    list_filter = (
        "saved_for_later",
    )

    search_fields = (
        "product__name",
        "cart__user__username",
    )


# =========================================
# ADDRESS
# =========================================

@admin.register(Address)
class AddressAdmin(ModelAdmin):

    list_display = (
        "id",
        "full_name",
        "user",
        "phone",
        "city",
        "state",
        "pincode",
        "is_default",
    )

    list_filter = (
        "state",
        "city",
        "is_default",
    )

    search_fields = (
        "full_name",
        "user__username",
        "phone",
        "pincode",
    )


# =========================================
# ORDER ITEM INLINE
# =========================================

class OrderItemInline(TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product",
        "product_name",
        "price",
        "quantity",
        "total_price",
    )

    can_delete = False

    show_change_link = False


# =========================================
# ORDER
# =========================================

@admin.register(Order)
class OrderAdmin(ModelAdmin):

    list_display = (
        "order_id",
        "customer_name",
        "total_amount",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "user__username",
        "user__email",
        "address__full_name",
        "address__phone",
    )

    readonly_fields = (
        "user",
        "address",
        "total_amount",
        "created_at",
        "updated_at",
    )

    list_editable = (
        "status",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 20

    inlines = (
        OrderItemInline,
    )

    fieldsets = (

        (
            "Order Information",
            {
                "fields": (
                    "user",
                    "total_amount",
                    "status",
                )
            },
        ),

        (
            "Delivery Information",
            {
                "fields": (
                    "address",
                )
            },
        ),

        (
            "Order Timeline",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),

    )

    @admin.display(
        description="Order ID",
        ordering="id",
    )
    def order_id(self, obj):

        return f"#{obj.id}"

    @admin.display(
        description="Customer",
        ordering="user__username",
    )
    def customer_name(self, obj):

        return obj.user.username


# =========================================
# ORDER ITEM
# =========================================

@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):

    list_display = (
        "id",
        "order",
        "product_name",
        "price",
        "quantity",
        "total_price",
    )

    search_fields = (
        "product_name",
        "order__user__username",
    )