import requests

from datetime import timedelta

from django.conf import settings


def send_whatsapp_message(phone, customer_name, order):

    phone = phone.strip()

    if phone.startswith("+"):
        phone = phone[1:]

    if not phone.startswith("91"):
        phone = "91" + phone


    expected_delivery = (
        order.created_at + timedelta(days=3)
    ).strftime("%d %b %Y")


    url = (
        f"https://graph.facebook.com/"
        f"{settings.WHATSAPP_API_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )


    headers = {

        "Authorization":
            f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",

        "Content-Type":
            "application/json",

    }


    data = {

        "messaging_product": "whatsapp",

        "to": phone,

        "type": "template",

        "template": {

            "name": "sudesh_order_confirmation",

            "language": {

                "code": "en"

            },

            "components": [

                {

                    "type": "body",

                    "parameters": [

                        {

                            "type": "text",

                            "text": customer_name

                        },

                        {

                            "type": "text",

                            "text": str(order.id)

                        },

                        {

                            "type": "text",

                            "text": order.payment_method

                        },

                        {

                            "type": "text",

                            "text": str(order.total_amount)

                        },

                        {

                            "type": "text",

                            "text": order.status

                        },

                        {

                            "type": "text",

                            "text": expected_delivery

                        }

                    ]

                }

            ]

        }

    }


    response = requests.post(

        url,

        headers=headers,

        json=data,

        timeout=20,

    )


    print("Status Code :", response.status_code)

    print("Response :", response.text)


    return response