from django.urls import path

from . import views


urlpatterns = [

    # =====================================
    # HOME
    # =====================================

    path(
        "",
        views.home,
        name="home"
    ),


    # =====================================
    # SECURE AUTHENTICATION
    # =====================================

    path(
        "login/",
        views.login,
        name="login"
    ),

    path(
        "verify-otp/",
        views.verify_otp,
        name="verify_otp"
    ),

    path(
        "resend-otp/",
        views.resend_otp,
        name="resend_otp"
    ),

    path(
        "forgot-password/",
        views.forgot_password,
        name="forgot_password"
    ),

    path(
        "reset-password/<uidb64>/<token>/",
        views.reset_password,
        name="reset_password"
    ),

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "check-email/",
        views.check_email,
        name="check_email"
    ),


    # =====================================
    # PRODUCT / CATEGORY
    # =====================================

    path(
        "category/<int:id>/",
        views.category_products,
        name="category_products"
    ),

    path(
        "product/<int:id>/",
        views.product_detail,
        name="product_detail"
    ),

    path(
        "product/<int:id>/review/",
        views.add_product_review,
        name="add_product_review"
    ),

    path(
        "search/",
        views.product_search,
        name="product_search"
    ),


    # =====================================
    # CART
    # =====================================

    path(
        "add-to-cart/<int:id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),

    path(
        "cart/",
        views.cart_page,
        name="cart"
    ),

    path(
        "update-cart/<int:id>/",
        views.update_cart_quantity,
        name="update_cart_quantity"
    ),

    path(
        "remove-cart/<int:id>/",
        views.remove_cart_item,
        name="remove_cart_item"
    ),

    path(
        "save-for-later/<int:id>/",
        views.save_for_later,
        name="save_for_later"
    ),

    path(
        "move-to-cart/<int:id>/",
        views.move_to_cart,
        name="move_to_cart"
    ),


    # =====================================
    # CHECKOUT / ORDERS
    # =====================================

    path(
        "checkout/",
        views.checkout,
        name="checkout"
    ),

    path(
        "order-success/<int:id>/",
        views.order_success,
        name="order_success"
    ),

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders"
    ),

    path(
        "order/<int:id>/",
        views.order_detail,
        name="order_detail"
    ),

    path(
        "order/<int:id>/invoice/",
        views.download_invoice,
        name="download_invoice"
    ),

    path(
        "cancel-order/<int:id>/",
        views.cancel_order,
        name="cancel_order"
    ),


    # =====================================
    # ACCOUNT
    # =====================================

    path(
        "my-account/",
        views.my_account,
        name="my_account"
    ),


    # =====================================
    # WISHLIST
    # =====================================

    path(
        "wishlist/",
        views.wishlist,
        name="wishlist"
    ),

    path(
        "wishlist/add/<int:id>/",
        views.add_to_wishlist,
        name="add_to_wishlist"
    ),

    path(
        "wishlist/remove/<int:id>/",
        views.remove_from_wishlist,
        name="remove_from_wishlist"
    ),
    path(
        "payment/",
        views.payment_page,
        name="payment_page"
    ),

    path(
        "payment/complete/",
        views.complete_payment,
        name="complete_payment"
    ),

    path(
        "payment/complete/",
        views.complete_payment,
        name="complete_payment"
    ),

]