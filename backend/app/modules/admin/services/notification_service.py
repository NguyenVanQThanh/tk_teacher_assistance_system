# File Name: notification_service.py
# Description: Service for generating temporary passwords and describing credential hand-off.
# Created At: 2026-09-29
# Created By: Tam Khang
# Updated At: 2026-11-15
# Updated By: AI Agent

import logging
import secrets
from typing import Dict, Any, Optional

logger = logging.getLogger("admin.notifications")


# Unambiguous alphabets (no 0/O, 1/l/I) so a password can be read out or typed from paper.
_UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_LOWER = "abcdefghijkmnopqrstuvwxyz"
_DIGITS = "23456789"
_SYMBOLS = "@#$%&*+=?"
PASSWORD_LENGTH = 12

class NotificationService:
    @staticmethod
    def generate_default_password() -> str:
        """
        Generate a 12-character random temporary password using `secrets`, guaranteed to contain
        at least one uppercase letter, lowercase letter, digit and symbol.
        """
        chars = [secrets.choice(_UPPER), secrets.choice(_LOWER), secrets.choice(_DIGITS), secrets.choice(_SYMBOLS)]
        pool = _UPPER + _LOWER + _DIGITS + _SYMBOLS
        chars += [secrets.choice(pool) for _ in range(PASSWORD_LENGTH - len(chars))]
        secrets.SystemRandom().shuffle(chars)
        return "".join(chars)

    @staticmethod
    def send_password_notification(
        full_name: str,
        password: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        action: str = "create"
    ) -> Dict[str, Any]:
        """
        Describe the credential hand-off. No SMS gateway exists, so nothing is sent: the admin
        must pass the temporary password on securely. The password is never logged.
        """
        logger.info("Temporary password issued: action=%s, delivery=manual", action)
        return {
            "sent": False,
            "channel": "Manual hand-off",
            "recipient": phone or email or "Internal User",
            "message": "No SMS or email was sent. Share the temporary password with the user securely."
        }
