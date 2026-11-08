import hmac
from hashlib import sha256

import razorpay

from ..config import settings


def get_client() -> razorpay.Client | None:
    if not settings.gateway_configured:
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount_paise: int, receipt: str) -> dict:
    client = get_client()
    if client is None:
        raise RuntimeError("Razorpay keys are not configured")
    return client.order.create(
        {"amount": amount_paise, "currency": "INR", "receipt": receipt}
    )


def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, signature: str) -> bool:
    """Razorpay sends order_id|payment_id signed with your key secret.
    Recomputing the HMAC client-side is how you reject forged success calls."""
    client = get_client()
    if client is None:
        return False
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except Exception:
        return False
