from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.enums import (
    TA_CENTER,
    TA_RIGHT,
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from django.contrib.auth.models import User

from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout,
)

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import (
    Product,
    Profile,
    Category,
    Cart,
    CartItem,
    Wishlist,
    Address,
    Order,
    OrderItem,
    ProductReview,
)

import re

from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

import random
import time

from django.core.mail import send_mail
from django.conf import settings

from django.contrib.auth.tokens import (
    default_token_generator,
)

from django.contrib.auth.password_validation import (
    validate_password,
)

from django.core.exceptions import ValidationError

from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode,
)

from django.utils.encoding import (
    force_bytes,
    force_str,
)

from .utils import send_whatsapp_message
 
 

# =========================================
# HOME
# =========================================

def home(request):

    products = Product.objects.all()

    categories = Category.objects.all()

    return render(
        request,
        "home.html",
        {
            "products": products,
            "categories": categories,
        }
    )


# =========================================
# LOGIN
# =========================================

def login(request):

    if request.user.is_authenticated:

        return redirect("home")


    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )


        # =================================
        # VALIDATE INPUT
        # =================================

        if not email or not password:

            messages.error(
                request,
                "Email and password are required."
            )

            return redirect("login")


        # =================================
        # FIND USER
        # =================================

        user_obj = User.objects.filter(
            email__iexact=email
        ).first()


        if user_obj is None:

            messages.error(
                request,
                "Invalid email or password."
            )

            return redirect("login")


        # =================================
        # VERIFY PASSWORD
        # =================================

        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )


        if user is None:

            messages.error(
                request,
                "Invalid email or password."
            )

            return redirect("login")


        # =================================
        # CREATE OTP
        # =================================

        otp = str(
            random.SystemRandom().randint(
                100000,
                999999
            )
        )


        # =================================
        # SAVE PENDING LOGIN IN SESSION
        # =================================

        request.session[
            "pending_login_user_id"
        ] = user.id

        request.session[
            "login_otp"
        ] = otp

        request.session[
            "login_otp_created_at"
        ] = int(time.time())

        request.session[
            "login_otp_attempts"
        ] = 0

        request.session[
            "login_otp_last_sent"
        ] = int(time.time())


        # =================================
        # SEND OTP EMAIL
        # =================================

        try:

            send_mail(
                subject=(
                    "Sudesh Bazaar Login OTP"
                ),
                message=(
                    f"Hello {user.first_name or user.username},\n\n"
                    f"Your Sudesh Bazaar login OTP is: {otp}\n\n"
                    "This OTP is valid for 5 minutes.\n"
                    "Do not share this OTP with anyone.\n\n"
                    "Sudesh Bazaar"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[
                    user.email
                ],
                fail_silently=False,
            )

        except Exception:

            request.session.pop(
                "pending_login_user_id",
                None
            )

            request.session.pop(
                "login_otp",
                None
            )

            messages.error(
                request,
                "Unable to send OTP email. Please try again."
            )

            return redirect("login")


        return redirect(
            "verify_otp"
        )


    return render(
        request,
        "login.html"
    )


# =========================================
# VERIFY LOGIN OTP
# =========================================

def verify_otp(request):

    if request.user.is_authenticated:

        return redirect("home")


    user_id = request.session.get(
        "pending_login_user_id"
    )

    stored_otp = request.session.get(
        "login_otp"
    )

    otp_created_at = request.session.get(
        "login_otp_created_at"
    )


    if (
        not user_id
        or not stored_otp
        or not otp_created_at
    ):

        messages.error(
            request,
            "Login session expired. Please login again."
        )

        return redirect("login")


    user = User.objects.filter(
        id=user_id
    ).first()


    if user is None:

        request.session.flush()

        return redirect("login")


    if request.method == "POST":

        entered_otp = request.POST.get(
            "otp",
            ""
        ).strip()


        # =================================
        # OTP FORMAT
        # =================================

        if (
            not entered_otp.isdigit()
            or len(entered_otp) != 6
        ):

            messages.error(
                request,
                "Enter a valid 6 digit OTP."
            )

            return redirect(
                "verify_otp"
            )


        current_time = int(
            time.time()
        )


        # =================================
        # OTP EXPIRY - 5 MINUTES
        # =================================

        if (
            current_time
            - int(otp_created_at)
            > 300
        ):

            messages.error(
                request,
                "OTP Expired. Please resend OTP."
            )

            return redirect(
                "verify_otp"
            )


        # =================================
        # OTP ATTEMPT LIMIT
        # =================================

        attempts = request.session.get(
            "login_otp_attempts",
            0
        )


        if attempts >= 5:

            messages.error(
                request,
                "Too many invalid OTP attempts. Please resend OTP."
            )

            return redirect(
                "verify_otp"
            )


        # =================================
        # INVALID OTP
        # =================================

        if entered_otp != stored_otp:

            request.session[
                "login_otp_attempts"
            ] = attempts + 1

            messages.error(
                request,
                "Invalid OTP."
            )

            return redirect(
                "verify_otp"
            )


        # =================================
        # OTP VERIFIED - ACTUAL LOGIN
        # =================================

        auth_login(
            request,
            user
        )


        request.session.pop(
            "pending_login_user_id",
            None
        )

        request.session.pop(
            "login_otp",
            None
        )

        request.session.pop(
            "login_otp_created_at",
            None
        )

        request.session.pop(
            "login_otp_attempts",
            None
        )

        request.session.pop(
            "login_otp_last_sent",
            None
        )


        messages.success(
            request,
            "Login successful."
        )


        return redirect(
            "home"
        )


    masked_email = (
        user.email[:2]
        + "***@"
        + user.email.split("@")[-1]
    )


    return render(
        request,
        "verify_otp.html",
        {
            "masked_email":
                masked_email
        }
    )


# =========================================
# RESEND LOGIN OTP
# =========================================

def resend_otp(request):

    if request.user.is_authenticated:

        return redirect("home")


    if request.method != "POST":

        return redirect(
            "verify_otp"
        )


    user_id = request.session.get(
        "pending_login_user_id"
    )


    if not user_id:

        messages.error(
            request,
            "Login session expired. Please login again."
        )

        return redirect("login")


    user = User.objects.filter(
        id=user_id
    ).first()


    if user is None:

        return redirect("login")


    current_time = int(
        time.time()
    )


    last_sent = request.session.get(
        "login_otp_last_sent",
        0
    )


    # =====================================
    # 30 SECOND RESEND COOLDOWN
    # =====================================

    if current_time - int(last_sent) < 30:

        wait_seconds = (
            30
            - (
                current_time
                - int(last_sent)
            )
        )

        messages.error(
            request,
            f"Please wait {wait_seconds} seconds before resending OTP."
        )

        return redirect(
            "verify_otp"
        )


    # =====================================
    # CREATE NEW OTP
    # =====================================

    otp = str(
        random.SystemRandom().randint(
            100000,
            999999
        )
    )


    try:

        send_mail(
            subject=(
                "Sudesh Bazaar New Login OTP"
            ),
            message=(
                f"Hello {user.first_name or user.username},\n\n"
                f"Your new login OTP is: {otp}\n\n"
                "This OTP is valid for 5 minutes.\n"
                "Your previous OTP is no longer valid.\n\n"
                "Sudesh Bazaar"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[
                user.email
            ],
            fail_silently=False,
        )

    except Exception:

        messages.error(
            request,
            "Unable to resend OTP. Please try again."
        )

        return redirect(
            "verify_otp"
        )


    request.session[
        "login_otp"
    ] = otp

    request.session[
        "login_otp_created_at"
    ] = current_time

    request.session[
        "login_otp_attempts"
    ] = 0

    request.session[
        "login_otp_last_sent"
    ] = current_time


    messages.success(
        request,
        "New OTP sent successfully."
    )


    return redirect(
        "verify_otp"
    )


# =========================================
# FORGOT PASSWORD
# =========================================

def forgot_password(request):

    if request.user.is_authenticated:

        return redirect("home")


    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()


        user = User.objects.filter(
            email__iexact=email
        ).first()


        if user:

            uid = urlsafe_base64_encode(
                force_bytes(user.pk)
            )

            token = (
                default_token_generator
                .make_token(user)
            )


            reset_url = request.build_absolute_uri(
                f"/reset-password/{uid}/{token}/"
            )


            try:

                send_mail(
                    subject=(
                        "Sudesh Bazaar Password Reset"
                    ),
                    message=(
                        f"Hello {user.first_name or user.username},\n\n"
                        "We received a request to reset your password.\n\n"
                        f"Reset your password using this link:\n"
                        f"{reset_url}\n\n"
                        "This password reset link expires in 15 minutes.\n"
                        "If you did not request this, ignore this email.\n\n"
                        "Sudesh Bazaar"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[
                        user.email
                    ],
                    fail_silently=False,
                )

            except Exception:

                pass


        messages.success(
            request,
            "If an account exists with this email, a password reset link has been sent."
        )


        return redirect(
            "forgot_password"
        )


    return render(
        request,
        "forgot_password.html"
    )


# =========================================
# RESET PASSWORD
# =========================================

def reset_password(
    request,
    uidb64,
    token
):

    if request.user.is_authenticated:

        return redirect("home")


    try:

        user_id = force_str(
            urlsafe_base64_decode(
                uidb64
            )
        )

        user = User.objects.get(
            pk=user_id
        )

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist
    ):

        user = None


    if (
        user is None
        or not default_token_generator.check_token(
            user,
            token
        )
    ):

        return render(
            request,
            "reset_password.html",
            {
                "invalid_link": True
            }
        )


    if request.method == "POST":

        new_password = request.POST.get(
            "new_password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )


        if new_password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "reset_password.html"
            )


        try:

            validate_password(
                new_password,
                user=user
            )

        except ValidationError as error:

            for message in error.messages:

                messages.error(
                    request,
                    message
                )


            return render(
                request,
                "reset_password.html"
            )


        user.set_password(
            new_password
        )

        user.save(
            update_fields=[
                "password"
            ]
        )


        messages.success(
            request,
            "Password Reset Successfully. Please login with your new password."
        )


        return redirect(
            "login"
        )


    return render(
        request,
        "reset_password.html"
    )

# =========================================
# REGISTER
# =========================================

def register(request):

    if request.method == "POST":

        firstname = request.POST.get(
            "firstname"
        ).strip()

        lastname = request.POST.get(
            "lastname"
        ).strip()

        username = request.POST.get(
            "username"
        ).strip()

        email = request.POST.get(
            "email"
        ).strip()

        phone = request.POST.get(
            "phone"
        ).strip()

        password = request.POST.get(
            "password"
        )

        confirm_password = request.POST.get(
            "confirm_password"
        )


        # FIRST NAME

        if not firstname:

            messages.error(
                request,
                "First Name is required"
            )

            return render(
                request,
                "register.html"
            )


        # LAST NAME

        if not lastname:

            messages.error(
                request,
                "Last Name is required"
            )

            return render(
                request,
                "register.html"
            )


        # USERNAME

        if not username:

            messages.error(
                request,
                "Username is required"
            )

            return render(
                request,
                "register.html"
            )


        # EMAIL FORMAT

        email_pattern = (
            r'^[\w\.-]+@[\w\.-]+\.\w+$'
        )


        if not re.match(
            email_pattern,
            email
        ):

            messages.error(
                request,
                "Enter Valid Email"
            )

            return render(
                request,
                "register.html"
            )


        # EMAIL EXISTS

        if User.objects.filter(
            email__iexact=email
        ).exists():

            return render(
                request,
                "register.html",
                {
                    "email_error":
                        "Email already exists",

                    "firstname":
                        firstname,

                    "lastname":
                        lastname,

                    "username":
                        username,

                    "email":
                        email,

                    "phone":
                        phone,
                }
            )


        # PHONE VALIDATION

        if not phone.isdigit():

            messages.error(
                request,
                "Phone Number should contain only numbers"
            )

            return render(
                request,
                "register.html"
            )


        if len(phone) != 10:

            messages.error(
                request,
                "Phone Number must be 10 digits"
            )

            return render(
                request,
                "register.html"
            )


        # PHONE EXISTS

        if Profile.objects.filter(
            phone=phone
        ).exists():

            return render(
                request,
                "register.html",
                {
                    "phone_error":
                        "Phone Number already exists",

                    "firstname":
                        firstname,

                    "lastname":
                        lastname,

                    "username":
                        username,

                    "email":
                        email,

                    "phone":
                        phone,
                }
            )


        # PASSWORD VALIDATION

        password_pattern = (
            r'^(?=.*[0-9])'
            r'(?=.*[@$!%*?&])'
            r'[A-Z].+$'
        )


        if not re.match(
            password_pattern,
            password
        ):

            messages.error(
                request,
                "Password must start with Capital Letter, "
                "contain Number and Special Character"
            )

            return render(
                request,
                "register.html"
            )


        # CONFIRM PASSWORD

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match"
            )

            return render(
                request,
                "register.html"
            )


        # UNIQUE USERNAME

        original_username = username

        count = 1


        while User.objects.filter(
            username=username
        ).exists():

            username = (
                f"{original_username}{count}"
            )

            count += 1


        # CREATE USER

        user = User.objects.create_user(
            first_name=firstname,
            last_name=lastname,
            username=username,
            email=email,
            password=password
        )


        # CREATE PROFILE

        Profile.objects.create(
            user=user,
            phone=phone
        )


        messages.success(
            request,
            "Account created successfully"
        )


        return redirect("login")


    return render(
        request,
        "register.html"
    )


# =========================================
# LOGOUT
# =========================================

def logout_view(request):

    logout(request)

    return redirect("home")


# =========================================
# ADD TO CART
# =========================================
def add_to_cart(request, id):

    if not request.user.is_authenticated:

        return JsonResponse({
            "login_required": True
        })


    product = get_object_or_404(
        Product,
        id=id
    )


    try:

        quantity = int(
            request.GET.get(
                "quantity",
                1
            )
        )

    except (TypeError, ValueError):

        quantity = 1


    if quantity < 1:

        quantity = 1


    if product.stock <= 0:

        return JsonResponse({
            "success": False,
            "message": "Product is out of stock"
        })


    if quantity > product.stock:

        return JsonResponse({
            "success": False,
            "message": "Requested quantity is not available"
        })


    cart, created = Cart.objects.get_or_create(
        user=request.user
    )


    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )


    # =====================================
    # FLIPKART STYLE CART QUANTITY
    # =====================================
    cart_item.saved_for_later = False

    cart_item.quantity = quantity

    cart_item.save()


    cart_count = sum(
        item.quantity
        for item in cart.items.all()
    )


    return JsonResponse({

        "success": True,

        "message":
            f"{product.name} added to cart",

        "cart_count":
            cart_count,

        "quantity":
            cart_item.quantity

    })

# =========================================
# CHECK EMAIL
# =========================================

def check_email(request):

    email = request.GET.get(
        "email"
    )


    exists = User.objects.filter(
        email__iexact=email
    ).exists()


    return JsonResponse({
        "exists": exists
    })


# =========================================
# CATEGORY PRODUCTS
# =========================================

def category_products(request, id):

    category = get_object_or_404(
        Category,
        id=id
    )

    products = Product.objects.filter(
        category=category
    )

    wishlist_product_ids = []

    if request.user.is_authenticated:

        wishlist_product_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list(
                "product_id",
                flat=True
            )
        )

    return render(
        request,
        "category_products.html",
        {
            "category": category,
            "products": products,
            "wishlist_product_ids":
                wishlist_product_ids,
        }
    )


# =========================================
# PRODUCT DETAIL
# =========================================

def product_detail(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )


    # =====================================
    # PRODUCT REVIEWS
    # =====================================

    reviews = ProductReview.objects.filter(
        product=product
    ).select_related(
        "user"
    )


    # =====================================
    # REVIEW SUMMARY
    # =====================================

    reviews_count = reviews.count()


    total_rating = sum(
        review.rating
        for review in reviews
    )


    if reviews_count > 0:

        average_rating = round(
            total_rating / reviews_count,
            1
        )

    else:

        average_rating = 0


    # =====================================
    # USER REVIEW INFORMATION
    # =====================================

    can_review = False

    user_review = None


    if request.user.is_authenticated:


        # =================================
        # CHECK DELIVERED ORDER
        # =================================

        can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__status="Delivered",
            product=product,
        ).exists()


        # =================================
        # EXISTING USER REVIEW
        # =================================

        user_review = ProductReview.objects.filter(
            product=product,
            user=request.user,
        ).first()


    # =====================================
    # PRODUCT DETAIL PAGE
    # =====================================

    return render(
        request,
        "product_detail.html",
        {
            "product": product,

            "reviews": reviews,

            "reviews_count": reviews_count,

            "average_rating": average_rating,

            "can_review": can_review,

            "user_review": user_review,
        }
    )


# =========================================
# CART PAGE
# =========================================
@login_required
def cart_page(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_items = cart.items.select_related(
        "product",
        "product__category"
    ).filter(
        saved_for_later=False
    )

    saved_items = cart.items.select_related(
        "product",
        "product__category"
    ).filter(
        saved_for_later=True
    )

    subtotal = sum(
        item.total_price
        for item in cart_items
    )

    cart_count = sum(
        item.quantity
        for item in cart_items
    )

    return render(
        request,
        "cart.html",
        {
            "cart": cart,
            "cart_items": cart_items,
            "saved_items": saved_items,
            "subtotal": subtotal,
            "cart_count": cart_count,
        }
    )

# =========================================
# UPDATE CART QUANTITY
# =========================================

def update_cart_quantity(request, id):

    if not request.user.is_authenticated:

        return JsonResponse({
            "login_required": True
        })


    cart_item = get_object_or_404(
        CartItem,
        id=id,
        cart__user=request.user
    )


    action = request.GET.get(
        "action"
    )


    if action == "plus":

        if (
            cart_item.quantity
            < cart_item.product.stock
        ):

            cart_item.quantity += 1

            cart_item.save()

        else:

            return JsonResponse({
                "success": False,
                "message":
                    "Maximum available stock reached"
            })


    elif action == "minus":

        if cart_item.quantity > 1:

            cart_item.quantity -= 1

            cart_item.save()


    cart = cart_item.cart


    cart_count = sum(
        item.quantity
        for item in cart.items.all()
    )


    subtotal = sum(
        item.total_price
        for item in cart.items.all()
    )


    return JsonResponse({
        "success": True,

        "quantity":
            cart_item.quantity,

        "item_total":
            float(cart_item.total_price),

        "cart_count":
            cart_count,

        "subtotal":
            float(subtotal),
    })


# =========================================
# REMOVE CART ITEM
# =========================================

def remove_cart_item(request, id):

    if not request.user.is_authenticated:

        return JsonResponse({
            "login_required": True
        })


    cart_item = get_object_or_404(
        CartItem,
        id=id,
        cart__user=request.user
    )


    product_name = (
        cart_item.product.name
    )


    cart = cart_item.cart


    cart_item.delete()


    cart_items = cart.items.all()


    cart_count = sum(
        item.quantity
        for item in cart_items
    )


    subtotal = sum(
        item.total_price
        for item in cart_items
    )


    return JsonResponse({
        "success": True,

        "message":
            f"{product_name} removed from cart",

        "cart_count":
            cart_count,

        "subtotal":
            float(subtotal),

        "cart_empty":
            not cart_items.exists(),
    })

def save_for_later(request, id):

    if not request.user.is_authenticated:

        return JsonResponse({
            "login_required": True
        })

    cart_item = get_object_or_404(
        CartItem,
        id=id,
        cart__user=request.user
    )

    cart_item.saved_for_later = True

    cart_item.save()

    cart = cart_item.cart

    active_items = cart.items.filter(
        saved_for_later=False
    )

    cart_count = sum(
        item.quantity
        for item in active_items
    )

    subtotal = sum(
        item.total_price
        for item in active_items
    )

    return JsonResponse({
        "success": True,
        "message": (
            f"{cart_item.product.name} "
            f"saved for later"
        ),
        "cart_count": cart_count,
        "subtotal": float(subtotal),
        "cart_empty": not active_items.exists(),
    })

def move_to_cart(request, id):

    if not request.user.is_authenticated:
        return JsonResponse({
            "login_required": True
        })

    cart_item = get_object_or_404(
        CartItem,
        id=id,
        cart__user=request.user,
        saved_for_later=True
    )

    if cart_item.product.stock < 1:
        return JsonResponse({
            "success": False,
            "message": "Product is out of stock"
        })

    cart_item.saved_for_later = False
    cart_item.quantity = 1
    cart_item.save()

    active_items = cart_item.cart.items.filter(
        saved_for_later=False
    )

    cart_count = sum(
        item.quantity
        for item in active_items
    )

    subtotal = sum(
        item.total_price
        for item in active_items
    )

    return JsonResponse({
        "success": True,
        "message": f"{cart_item.product.name} moved to cart",
        "cart_count": cart_count,
        "subtotal": float(subtotal),
    })

@login_required
def checkout(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_items = cart.items.filter(
        saved_for_later=False
    ).select_related(
        "product"
    )


    # =========================================
    # EMPTY CART
    # =========================================

    if not cart_items.exists():

        messages.error(
            request,
            "Your cart is empty"
        )

        return redirect("cart")


    # =========================================
    # TOTAL AMOUNT
    # =========================================

    subtotal = sum(
        item.total_price
        for item in cart_items
    )


    cart_count = sum(
        item.quantity
        for item in cart_items
    )


    # =========================================
    # SAVED ADDRESSES
    # =========================================

    all_addresses = Address.objects.filter(
        user=request.user
    ).order_by(
        "-is_default",
        "-created_at"
    )


    addresses = []

    seen_addresses = set()


    for saved_address in all_addresses:

        address_key = (

            saved_address.full_name
            .strip()
            .lower(),

            saved_address.phone.strip(),

            saved_address.address_line
            .strip()
            .lower(),

            saved_address.city
            .strip()
            .lower(),

            saved_address.state
            .strip()
            .lower(),

            saved_address.pincode.strip(),

        )


        if address_key not in seen_addresses:

            seen_addresses.add(
                address_key
            )

            addresses.append(
                saved_address
            )


    # =========================================
    # CHECKOUT CONTEXT
    # =========================================

    context = {

        "cart_items": cart_items,

        "subtotal": subtotal,

        "cart_count": cart_count,

        "addresses": addresses,

    }


    # =========================================
    # PLACE ORDER
    # =========================================

    if request.method == "POST":

        selected_address_id = request.POST.get(
            "selected_address"
        )


        payment_method = request.POST.get(
            "payment_method",
            ""
        ).strip()


        # =====================================
        # PAYMENT METHOD VALIDATION
        # =====================================

        if payment_method not in [
            "COD",
            "ONLINE",
        ]:

            messages.error(
                request,
                "Please select a payment method"
            )

            return render(
                request,
                "checkout.html",
                context
            )


        # =====================================
        # USE SAVED ADDRESS
        # =====================================

        if selected_address_id:

            address = get_object_or_404(
                Address,
                id=selected_address_id,
                user=request.user
            )


        # =====================================
        # CREATE NEW ADDRESS
        # =====================================

        else:

            full_name = request.POST.get(
                "full_name",
                ""
            ).strip()

            phone = request.POST.get(
                "phone",
                ""
            ).strip()

            address_line = request.POST.get(
                "address_line",
                ""
            ).strip()

            city = request.POST.get(
                "city",
                ""
            ).strip()

            state = request.POST.get(
                "state",
                ""
            ).strip()

            pincode = request.POST.get(
                "pincode",
                ""
            ).strip()


            if (
                not full_name
                or not phone
                or not address_line
                or not city
                or not state
                or not pincode
            ):

                messages.error(
                    request,
                    "Select a saved address or enter new address"
                )

                return render(
                    request,
                    "checkout.html",
                    context
                )


            if (
                not phone.isdigit()
                or len(phone) != 10
            ):

                messages.error(
                    request,
                    "Enter valid 10 digit phone number"
                )

                return render(
                    request,
                    "checkout.html",
                    context
                )


            if (
                not pincode.isdigit()
                or len(pincode) != 6
            ):

                messages.error(
                    request,
                    "Enter valid 6 digit pincode"
                )

                return render(
                    request,
                    "checkout.html",
                    context
                )


            Address.objects.filter(
                user=request.user,
                is_default=True
            ).update(
                is_default=False
            )


            address = Address.objects.create(

                user=request.user,

                full_name=full_name,

                phone=phone,

                address_line=address_line,

                city=city,

                state=state,

                pincode=pincode,

                is_default=True,

            )


        # =====================================
        # CHECK STOCK
        # =====================================

        for item in cart_items:

            if item.quantity > item.product.stock:

                messages.error(
                    request,
                    (
                        f"{item.product.name} "
                        "has insufficient stock"
                    )
                )

                return redirect("cart")


        # =====================================
        # CASH ON DELIVERY
        # =====================================

        if payment_method == "COD":

            order = Order.objects.create(

                user=request.user,

                address=address,

                total_amount=subtotal,

                status="Placed",

                payment_method="COD",

                payment_status="Pending",

            )


            for item in cart_items:

                product = item.product


                OrderItem.objects.create(

                    order=order,

                    product=product,

                    product_name=product.name,

                    price=product.price,

                    quantity=item.quantity,

                )


                product.stock -= item.quantity

                product.save(
                    update_fields=[
                        "stock"
                    ]
                )


            cart_items.delete()


            messages.success(
                request,
                "Order placed successfully"
            )


            return redirect(
                "order_success",
                id=order.id
            )


        # =====================================
        # ONLINE PAYMENT
        # =====================================

        request.session["checkout_address_id"] = address.id

        request.session["checkout_payment_method"] = "ONLINE"

        return redirect("payment_page")

    return render(
        request,
        "checkout.html",
        context
    )

@login_required
def payment_page(request):

    address_id = request.session.get(
        "checkout_address_id"
    )

    payment_method = request.session.get(
        "checkout_payment_method"
    )

    if not address_id or payment_method != "ONLINE":

        messages.error(
            request,
            "Payment session expired."
        )

        return redirect("checkout")


    cart = get_object_or_404(
        Cart,
        user=request.user
    )

    cart_items = cart.items.filter(
        saved_for_later=False
    ).select_related(
        "product"
    )

    subtotal = sum(
        item.total_price
        for item in cart_items
    )

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    return render(

        request,

        "payment.html",

        {

            "cart_items": cart_items,

            "subtotal": subtotal,

            "address": address,

        }

    )

@login_required
def complete_payment(request):

    if request.method != "POST":

        return redirect("checkout")


    address_id = request.session.get(
        "checkout_address_id"
    )


    if not address_id:

        messages.error(
            request,
            "Payment session expired."
        )

        return redirect("checkout")


    address = get_object_or_404(

        Address,

        id=address_id,

        user=request.user

    )


    cart = get_object_or_404(

        Cart,

        user=request.user

    )


    cart_items = cart.items.filter(

        saved_for_later=False

    ).select_related(

        "product"

    )


    if not cart_items.exists():

        messages.error(

            request,

            "Your cart is empty."

        )

        return redirect("cart")


    subtotal = sum(

        item.total_price

        for item in cart_items

    )


    transaction_id = (

        "TXN"

        + str(

            random.randint(

                10000000,

                99999999

            )

        )

    )


    order = Order.objects.create(

        user=request.user,

        address=address,

        total_amount=subtotal,

        status="Confirmed",

        payment_method="ONLINE",

        payment_status="Paid",

        razorpay_payment_id=transaction_id,

    )


    for item in cart_items:

        product = item.product


        OrderItem.objects.create(

            order=order,

            product=product,

            product_name=product.name,

            price=product.price,

            quantity=item.quantity,

        )


        product.stock -= item.quantity

        product.save(

            update_fields=[

                "stock"

            ]

        )


    cart_items.delete()


    request.session.pop(

        "checkout_address_id",

        None

    )

    request.session.pop(

        "checkout_payment_method",

        None

    )


    messages.success(

        request,

        "Payment Successful."

    )
    try:

        send_whatsapp_message(

            phone=str(order.address.phone),

            customer_name=order.address.full_name,

            order=order,

        )

    except Exception as e:

        print("WhatsApp Error :", e)


    return redirect(

        "order_success",

        id=order.id

    )

 

@login_required
def order_success(request, id):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product"
        ).select_related(
            "address"
        ),
        id=id,
        user=request.user
    )

    return render(
        request,
        "order_success.html",
        {
            "order": order
        }
    )

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).select_related(
        "address"
    ).prefetch_related(
        "items__product"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "my_orders.html",
        {
            "orders": orders
        }
    )

# =========================================
# ORDER DETAIL
# =========================================

@login_required
def order_detail(request, id):

    order = get_object_or_404(
        Order.objects.select_related(
            "address",
            "user"
        ).prefetch_related(
            "items__product"
        ),
        id=id,
        user=request.user
    )

    return render(
        request,
        "order_detail.html",
        {
            "order": order
        }
    )

# =========================================
# CANCEL ORDER
# =========================================

@login_required
def cancel_order(request, id):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__product"
        ),
        id=id,
        user=request.user
    )

    # =====================================
    # CHECK CANCEL ELIGIBILITY
    # =====================================

    if not order.can_cancel:

        messages.error(
            request,
            "This order can no longer be cancelled."
        )

        return redirect(
            "order_detail",
            id=order.id
        )

    # =====================================
    # POST REQUEST
    # =====================================

    if request.method == "POST":

        cancel_reason = request.POST.get(
            "cancel_reason",
            ""
        ).strip()

        cancel_note = request.POST.get(
            "cancel_note",
            ""
        ).strip()

        # =================================
        # VALIDATE CANCEL REASON
        # =================================

        valid_reasons = [
            choice[0]
            for choice
            in Order.CANCEL_REASON_CHOICES
        ]

        if cancel_reason not in valid_reasons:

            messages.error(
                request,
                "Please select a valid cancellation reason."
            )

            return redirect(
                "cancel_order",
                id=order.id
            )

        # =================================
        # OTHER REASON NOTE REQUIRED
        # =================================

        if (
            cancel_reason == "Other"
            and not cancel_note
        ):

            messages.error(
                request,
                "Please enter your cancellation reason."
            )

            return redirect(
                "cancel_order",
                id=order.id
            )

        # =================================
        # RESTORE PRODUCT STOCK
        # =================================

        for item in order.items.all():

            product = item.product

            if product:

                product.stock += item.quantity

                product.save(
                    update_fields=[
                        "stock"
                    ]
                )

        # =================================
        # CANCEL ORDER
        # =================================

        order.status = "Cancelled"

        order.cancel_reason = cancel_reason

        order.cancel_note = (
            cancel_note or None
        )

        order.cancelled_at = timezone.now()

        order.save(
            update_fields=[
                "status",
                "cancel_reason",
                "cancel_note",
                "cancelled_at",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"Order #{order.id} has been cancelled successfully."
        )

        return redirect(
            "order_detail",
            id=order.id
        )

    # =====================================
    # CANCEL ORDER PAGE
    # =====================================

    return render(
        request,
        "cancel_order.html",
        {
            "order": order,
            "cancel_reasons":
                Order.CANCEL_REASON_CHOICES,
        }
    )
# =========================================
# PRODUCT SEARCH
# =========================================

def product_search(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    sort = request.GET.get(
        "sort",
        ""
    )

    stock = request.GET.get(
        "stock",
        ""
    )


    products = Product.objects.none()


    # =====================================
    # SEARCH PRODUCTS
    # =====================================

    if query:

        products = Product.objects.filter(

            Q(name__icontains=query)

            |

            Q(category__name__icontains=query)

        ).select_related(
            "category"
        )


        # =================================
        # STOCK FILTER
        # =================================

        if stock == "in_stock":

            products = products.filter(
                stock__gt=0
            )


        elif stock == "out_of_stock":

            products = products.filter(
                stock=0
            )


        # =================================
        # PRODUCT SORT
        # =================================

        if sort == "price_low":

            products = products.order_by(
                "price"
            )


        elif sort == "price_high":

            products = products.order_by(
                "-price"
            )


        elif sort == "name_az":

            products = products.annotate(
                lower_name=Lower("name")
            ).order_by(
                "lower_name"
            )


        elif sort == "name_za":

            products = products.annotate(
                lower_name=Lower("name")
            ).order_by(
                "-lower_name"
            )


        else:

            products = products.order_by(
                "id"
            )


    # =====================================
    # SEARCH PAGE
    # =====================================

    return render(
        request,
        "product_search.html",
        {
            "query": query,

            "products": products,

            "selected_sort": sort,

            "selected_stock": stock,
        }
    )
# =========================================
# MY ACCOUNT
# =========================================

@login_required
def my_account(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # =====================================
    # UPDATE PROFILE
    # =====================================

    if request.method == "POST":

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()


        # =================================
        # REQUIRED VALIDATION
        # =================================

        if not first_name:

            messages.error(
                request,
                "First Name is required"
            )

            return redirect(
                "my_account"
            )


        if not last_name:

            messages.error(
                request,
                "Last Name is required"
            )

            return redirect(
                "my_account"
            )


        # =================================
        # PHONE VALIDATION
        # =================================

        if (
            not phone.isdigit()
            or len(phone) != 10
        ):

            messages.error(
                request,
                "Enter valid 10 digit phone number"
            )

            return redirect(
                "my_account"
            )


        # =================================
        # PHONE EXISTS
        # =================================

        if Profile.objects.filter(
            phone=phone
        ).exclude(
            user=request.user
        ).exists():

            messages.error(
                request,
                "Phone Number already exists"
            )

            return redirect(
                "my_account"
            )


        # =================================
        # UPDATE USER
        # =================================

        request.user.first_name = first_name

        request.user.last_name = last_name

        request.user.save(
            update_fields=[
                "first_name",
                "last_name",
            ]
        )


        # =================================
        # UPDATE PROFILE
        # =================================

        profile.phone = phone

        profile.save(
            update_fields=[
                "phone"
            ]
        )


        messages.success(
            request,
            "Profile updated successfully"
        )


        return redirect(
            "my_account"
        )


    # =====================================
    # ACCOUNT INFORMATION
    # =====================================

    addresses = Address.objects.filter(
        user=request.user,
        is_default=True
    )


    orders_count = Order.objects.filter(
        user=request.user
    ).count()


    return render(
        request,
        "my_account.html",
        {
            "profile": profile,
            "addresses": addresses,
            "orders_count": orders_count,
        }
    )

# =========================================
# ADD TO WISHLIST
# =========================================

def add_to_wishlist(request, id):

    if not request.user.is_authenticated:

        return JsonResponse(
            {
                "success": False,
                "login_required": True,
                "message": "Please login to use wishlist",
            }
        )

    product = get_object_or_404(
        Product,
        id=id
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    if wishlist_item:

        wishlist_item.delete()

        return JsonResponse(
            {
                "success": True,
                "added": False,
                "message":
                    "Product removed from wishlist",
            }
        )

    Wishlist.objects.create(
        user=request.user,
        product=product
    )

    return JsonResponse(
        {
            "success": True,
            "added": True,
            "message":
                "Product added to wishlist",
        }
    )


# =========================================
# WISHLIST PAGE
# =========================================

@login_required
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        "product",
        "product__category"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )


# =========================================
# REMOVE FROM WISHLIST
# =========================================

@login_required
def remove_from_wishlist(request, id):

    wishlist_item = get_object_or_404(
        Wishlist,
        id=id,
        user=request.user
    )

    product_name = (
        wishlist_item.product.name
    )

    wishlist_item.delete()

    messages.success(
        request,
        f"{product_name} removed from wishlist"
    )

    return redirect(
        "wishlist"
    )

# =========================================
# ADD / UPDATE PRODUCT REVIEW
# =========================================

@login_required
def add_product_review(request, id):

    product = get_object_or_404(
        Product,
        id=id
    )


    # =====================================
    # POST REQUEST ONLY
    # =====================================

    if request.method != "POST":

        return redirect(
            "product_detail",
            id=product.id
        )


    # =====================================
    # CHECK DELIVERED ORDER
    # =====================================

    has_delivered_order = (
        OrderItem.objects.filter(
            order__user=request.user,
            order__status="Delivered",
            product=product,
        ).exists()
    )


    if not has_delivered_order:

        messages.error(
            request,
            "Only customers who purchased and received this product can review it."
        )

        return redirect(
            "product_detail",
            id=product.id
        )


    # =====================================
    # GET REVIEW DATA
    # =====================================

    rating = request.POST.get(
        "rating",
        ""
    )

    review_text = request.POST.get(
        "review",
        ""
    ).strip()


    # =====================================
    # RATING VALIDATION
    # =====================================

    try:

        rating = int(rating)

    except (
        TypeError,
        ValueError
    ):

        messages.error(
            request,
            "Please select a valid rating."
        )

        return redirect(
            "product_detail",
            id=product.id
        )


    if rating not in [
        1,
        2,
        3,
        4,
        5,
    ]:

        messages.error(
            request,
            "Rating must be between 1 and 5."
        )

        return redirect(
            "product_detail",
            id=product.id
        )


    # =====================================
    # REVIEW VALIDATION
    # =====================================

    if not review_text:

        messages.error(
            request,
            "Please enter your review."
        )

        return redirect(
            "product_detail",
            id=product.id
        )


    if len(review_text) > 1000:

        messages.error(
            request,
            "Review cannot exceed 1000 characters."
        )

        return redirect(
            "product_detail",
            id=product.id
        )


    # =====================================
    # CREATE OR UPDATE REVIEW
    # =====================================

    product_review, created = (
        ProductReview.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                "rating": rating,
                "review": review_text,
            }
        )
    )


    # =====================================
    # SUCCESS MESSAGE
    # =====================================

    if created:

        messages.success(
            request,
            "Review added successfully."
        )

    else:

        messages.success(
            request,
            "Review updated successfully."
        )


    return redirect(
        "product_detail",
        id=product.id
    )
# =========================================
# PROFESSIONAL SUDESH BAZAAR TAX INVOICE
# =========================================

@login_required
def download_invoice(request, id):

    order = get_object_or_404(
        Order.objects.select_related(
            "address",
            "user"
        ).prefetch_related(
            "items__product"
        ),
        id=id,
        user=request.user
    )
    # =====================================
    # INVOICE ONLY FOR DELIVERED ORDERS
    # =====================================

    if order.status != "Delivered":

        messages.error(
            request,
            "Invoice is available only after the order is delivered."
        )

        return redirect(
            "order_detail",
            id=order.id
        )

    # =====================================
    # CANCELLED ORDER
    # =====================================

    if order.status == "Cancelled":

        messages.error(
            request,
            "Invoice is not available for cancelled orders."
        )

        return redirect(
            "order_detail",
            id=order.id
        )

    # =====================================
    # RESPONSE
    # =====================================

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="Sudesh_Bazaar_Invoice_{order.id}.pdf"'
    )

    # =====================================
    # DOCUMENT
    # =====================================

    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=35,
        bottomMargin=30,
    )

    elements = []

    styles = getSampleStyleSheet()

    # =====================================
    # COLORS
    # =====================================

    NAVY = colors.HexColor("#172337")

    BLUE = colors.HexColor("#2874F0")

    DARK = colors.HexColor("#111827")

    TEXT = colors.HexColor("#374151")

    MUTED = colors.HexColor("#6B7280")

    BORDER = colors.HexColor("#D9DEE7")

    LIGHT = colors.HexColor("#F8FAFC")

    LIGHT_BLUE = colors.HexColor("#EFF6FF")

    GREEN = colors.HexColor("#16A34A")

    WHITE = colors.white

    # =====================================
    # PARAGRAPH STYLES
    # =====================================

    brand_style = ParagraphStyle(
        "InvoiceBrand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        textColor=NAVY,
        spaceAfter=0,
    )

    tagline_style = ParagraphStyle(
        "InvoiceTagline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=12,
        textColor=MUTED,
    )

    invoice_title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=BLUE,
        alignment=TA_RIGHT,
    )

    invoice_number_style = ParagraphStyle(
        "InvoiceNumber",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=13,
        textColor=TEXT,
        alignment=TA_RIGHT,
    )

    label_style = ParagraphStyle(
        "InvoiceLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=12,
        textColor=MUTED,
    )

    value_style = ParagraphStyle(
        "InvoiceValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=TEXT,
    )

    value_bold_style = ParagraphStyle(
        "InvoiceValueBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=16,
        textColor=DARK,
    )

    section_style = ParagraphStyle(
        "InvoiceSection",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=15,
        textColor=NAVY,
    )

    table_header_style = ParagraphStyle(
        "InvoiceTableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=12,
        textColor=WHITE,
    )

    product_style = ParagraphStyle(
        "InvoiceProduct",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=15,
        textColor=DARK,
    )

    table_value_style = ParagraphStyle(
        "InvoiceTableValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=TEXT,
    )

    table_right_style = ParagraphStyle(
        "InvoiceTableRight",
        parent=table_value_style,
        alignment=TA_RIGHT,
    )

    table_center_style = ParagraphStyle(
        "InvoiceTableCenter",
        parent=table_value_style,
        alignment=TA_CENTER,
    )

    total_label_style = ParagraphStyle(
        "InvoiceTotalLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=TEXT,
    )

    total_value_style = ParagraphStyle(
        "InvoiceTotalValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=14,
        textColor=DARK,
        alignment=TA_RIGHT,
    )

    grand_label_style = ParagraphStyle(
        "InvoiceGrandLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=NAVY,
    )

    grand_value_style = ParagraphStyle(
        "InvoiceGrandValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=NAVY,
        alignment=TA_RIGHT,
    )

    footer_style = ParagraphStyle(
        "InvoiceFooter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=13,
        textColor=MUTED,
        alignment=TA_CENTER,
    )

    # =====================================
    # CUSTOMER DATA
    # =====================================

    address = order.address

    customer_name = (
        address.full_name
        or order.user.get_full_name()
        or order.user.username
    )

    customer_email = (
        order.user.email
        or "Not provided"
    )

    # =====================================
    # HEADER
    # =====================================

    brand_content = [

        Paragraph(
            "SUDESH BAZAAR",
            brand_style
        ),

        Spacer(
            1,
            3
        ),

        Paragraph(
            "Quality products. Better shopping.",
            tagline_style
        ),

    ]

    invoice_content = [

        Paragraph(
            "TAX INVOICE",
            invoice_title_style
        ),

        Spacer(
            1,
            6
        ),

        Paragraph(
            f"Invoice No: "
            f"<b>SB-INV-{order.id:05d}</b>"
            "<br/>"
            f"Invoice Date: "
            f"<b>{order.created_at.strftime('%d %b %Y')}</b>",
            invoice_number_style
        ),

    ]

    header_table = Table(
        [
            [
                brand_content,
                invoice_content
            ]
        ],
        colWidths=[
            300,
            210
        ]
    )

    header_table.setStyle(
        TableStyle(
            [

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

            ]
        )
    )

    elements.append(
        header_table
    )

    elements.append(
        Spacer(
            1,
            14
        )
    )

    # =====================================
    # HEADER LINE
    # =====================================

    header_line = Table(
        [[""]],
        colWidths=[510],
        rowHeights=[3]
    )

    header_line.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    BLUE
                ),

            ]
        )
    )

    elements.append(
        header_line
    )

    elements.append(
        Spacer(
            1,
            20
        )
    )

    # =====================================
    # BILLING + ORDER DETAILS
    # =====================================

    billing_content = [

        Paragraph(
            "BILL TO / DELIVERY ADDRESS",
            label_style
        ),

        Spacer(
            1,
            8
        ),

        Paragraph(
            customer_name,
            value_bold_style
        ),

        Paragraph(
            address.address_line,
            value_style
        ),

        Paragraph(
            f"{address.city}, "
            f"{address.state} - "
            f"{address.pincode}",
            value_style
        ),

        Spacer(
            1,
            5
        ),

        Paragraph(
            f"<b>Phone:</b> {address.phone}",
            value_style
        ),

        Paragraph(
            f"<b>Email:</b> {customer_email}",
            value_style
        ),

    ]

    order_content = [

        Paragraph(
            "ORDER DETAILS",
            label_style
        ),

        Spacer(
            1,
            8
        ),

        Paragraph(
            "Order ID",
            label_style
        ),

        Paragraph(
            f"#{order.id}",
            value_bold_style
        ),

        Spacer(
            1,
            4
        ),

        Paragraph(
            "Order Date",
            label_style
        ),

        Paragraph(
            order.created_at.strftime(
                "%d %b %Y"
            ),
            value_bold_style
        ),

        Spacer(
            1,
            4
        ),

        Paragraph(
            "Order Status",
            label_style
        ),

        Paragraph(
            f"<font color='#16A34A'>"
            f"<b>{order.status}</b>"
            f"</font>",
            value_bold_style
        ),

    ]

    details_table = Table(
        [
            [
                billing_content,
                order_content
            ]
        ],
        colWidths=[
            325,
            185
        ]
    )

    details_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    BORDER
                ),

                (
                    "LINEBEFORE",
                    (1, 0),
                    (1, 0),
                    0.7,
                    BORDER
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    18
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    18
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    16
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    16
                ),

            ]
        )
    )

    elements.append(
        details_table
    )

    elements.append(
        Spacer(
            1,
            24
        )
    )

    # =====================================
    # ORDER ITEMS
    # =====================================

    elements.append(
        Paragraph(
            "ORDER ITEMS",
            section_style
        )
    )

    elements.append(
        Spacer(
            1,
            8
        )
    )

    product_data = [

        [

            Paragraph(
                "PRODUCT",
                table_header_style
            ),

            Paragraph(
                "UNIT PRICE",
                table_header_style
            ),

            Paragraph(
                "QTY",
                table_header_style
            ),

            Paragraph(
                "AMOUNT",
                table_header_style
            ),

        ]

    ]

    for item in order.items.all():

        product_data.append(
            [

                Paragraph(
                    item.product_name,
                    product_style
                ),

                Paragraph(
                    f"Rs. {item.price:,.2f}",
                    table_right_style
                ),

                Paragraph(
                    str(item.quantity),
                    table_center_style
                ),

                Paragraph(
                    f"<b>Rs. "
                    f"{item.total_price:,.2f}</b>",
                    table_right_style
                ),

            ]
        )

    product_table = Table(
        product_data,
        colWidths=[
            245,
            105,
            55,
            105
        ],
        repeatRows=1
    )

    product_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),

                (
                    "ALIGN",
                    (2, 0),
                    (2, -1),
                    "CENTER"
                ),

                (
                    "ALIGN",
                    (3, 0),
                    (3, -1),
                    "RIGHT"
                ),

                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER
                ),

                (
                    "LINEBEFORE",
                    (1, 0),
                    (-1, -1),
                    0.6,
                    BORDER
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    12
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    12
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    10
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    10
                ),

                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, -1),
                    15
                ),

                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, -1),
                    15
                ),

            ]
        )
    )

    elements.append(
        product_table
    )

    elements.append(
        Spacer(
            1,
            20
        )
    )

    # =====================================
    # TOTAL SUMMARY
    # =====================================

    total_data = [

        [

            Paragraph(
                "Subtotal",
                total_label_style
            ),

            Paragraph(
                f"Rs. {order.total_amount:,.2f}",
                total_value_style
            ),

        ],

        [

            Paragraph(
                "Delivery Charges",
                total_label_style
            ),

            Paragraph(
                "<font color='#16A34A'>"
                "<b>FREE</b>"
                "</font>",
                total_value_style
            ),

        ],

        [

            Paragraph(
                "GRAND TOTAL",
                grand_label_style
            ),

            Paragraph(
                f"Rs. {order.total_amount:,.2f}",
                grand_value_style
            ),

        ],

    ]

    total_table = Table(
        total_data,
        colWidths=[
            180,
            150
        ],
        hAlign="RIGHT"
    )

    total_table.setStyle(
        TableStyle(
            [

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    12
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    12
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),

                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    NAVY
                ),

                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    LIGHT_BLUE
                ),

            ]
        )
    )

    elements.append(
        total_table
    )

    elements.append(
        Spacer(
            1,
            28
        )
    )

    # =====================================
    # THANK YOU
    # =====================================

    thank_you_table = Table(
        [

            [

                Paragraph(
                    "<b>Thank you for shopping "
                    "with Sudesh Bazaar.</b>"
                    "<br/>"
                    "We appreciate your business "
                    "and hope to serve you again.",
                    footer_style
                )

            ]

        ],
        colWidths=[
            510
        ]
    )

    thank_you_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    11
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    11
                ),

            ]
        )
    )

    elements.append(
        thank_you_table
    )

    elements.append(
        Spacer(
            1,
            8
        )
    )

    elements.append(
        Paragraph(
            "This is a computer generated invoice "
            "and does not require a signature.",
            footer_style
        )
    )

    # =====================================
    # BUILD PDF
    # =====================================

    document.build(
        elements
    )

    return response