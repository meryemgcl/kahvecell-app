import base64
import hashlib
import hmac
import io
import json
import os

import qrcode


QR_SECRET = os.getenv("QR_SECRET_KEY", "kahvecell-qr-development-secret")


def create_qr_payload(order_id: str, user_id: str, shop_id: str, created_at: str) -> tuple[dict, str, str]:
    unsigned = {
        "order_id": order_id,
        "user_id": user_id,
        "shop_id": shop_id,
        "created_at": created_at,
    }
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    signature = hmac.new(
        QR_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    payload = {**unsigned, "signature": signature}
    payload_json = json.dumps(payload, ensure_ascii=False)
    image = qrcode.make(payload_json)
    output = io.BytesIO()
    image.save(output, format="PNG")
    qr_base64 = base64.b64encode(output.getvalue()).decode("ascii")
    return payload, payload_json, f"data:image/png;base64,{qr_base64}"


def verify_qr_payload(payload: dict) -> bool:
    required = ("order_id", "user_id", "shop_id", "created_at", "signature")
    if any(field not in payload for field in required):
        return False

    unsigned = {
        field: payload[field]
        for field in ("order_id", "user_id", "shop_id", "created_at")
    }
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = hmac.new(
        QR_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, str(payload["signature"]))
