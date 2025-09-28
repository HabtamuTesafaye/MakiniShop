import uuid
from django.core.cache import cache

OTP_EXPIRY = 300  # 5 minutes

def generate_otp(user_id):
    otp = str(uuid.uuid4())[:6]
    cache.set(f"otp:{user_id}", otp, timeout=OTP_EXPIRY)
    return otp

def verify_otp(user_id, otp):
    cached = cache.get(f"otp:{user_id}")
    if cached and cached == otp:
        cache.delete(f"otp:{user_id}")
        return True
    return False
