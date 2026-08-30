# File Name: rate_limit.py
# Description: Custom in-memory login rate limiter to protect against brute-force attacks.
# Created At: 2026-07-17
# Created By: Tam Khang
# Updated At: 2026-07-17
# Updated By: Tam Khang

import time
from typing import Dict, Tuple

# In-memory store for failed login attempts
# Format: { phone: {"fail_count": int, "lock_until": float, "last_fail_time": float} }
_failed_attempts: Dict[str, dict] = {}

# Configuration
MAX_FAILURES = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
WINDOW_DURATION_SECONDS = 300   # 5 minutes

def check_rate_limit(phone: str) -> Tuple[bool, int]:
    """
    Checks if the given phone number is currently locked out.
    Returns a tuple: (is_blocked, retry_after_seconds)
    """
    now = time.time()
    record = _failed_attempts.get(phone)
    if not record:
        return False, 0
    
    # 1. Check if locked out
    lock_until = record.get("lock_until", 0.0)
    if now < lock_until:
        retry_after = int(lock_until - now)
        return True, max(1, retry_after)
    
    # 2. Lock has expired, check if we should reset it
    if lock_until > 0.0:
        # Lockout expired, reset counters
        record["fail_count"] = 0
        record["lock_until"] = 0.0
        
    return False, 0

def record_login_failure(phone: str) -> None:
    """
    Increments the failed login attempts count for the phone number.
    If it reaches MAX_FAILURES, locks it out for LOCKOUT_DURATION_SECONDS.
    """
    now = time.time()
    if phone not in _failed_attempts:
        _failed_attempts[phone] = {
            "fail_count": 0,
            "lock_until": 0.0,
            "last_fail_time": 0.0
        }
        
    record = _failed_attempts[phone]
    
    # Reset fail count if the last failure was outside the 5-minute window
    last_fail = record.get("last_fail_time", 0.0)
    if now - last_fail > WINDOW_DURATION_SECONDS:
        record["fail_count"] = 0
        
    record["fail_count"] += 1
    record["last_fail_time"] = now
    
    if record["fail_count"] >= MAX_FAILURES:
        record["lock_until"] = now + LOCKOUT_DURATION_SECONDS

def reset_login_failures(phone: str) -> None:
    """
    Resets the failed attempts count and lockout status for the phone number.
    Call this upon successful login.
    """
    if phone in _failed_attempts:
        _failed_attempts.pop(phone)
