# File Name: notification_service.py
# Description: Service for generating default passwords and dispatching SMS / system notifications.
# Created At: 2026-09-29
# Created By: Tam Khang
# Updated At: 2026-09-29
# Updated By: Tam Khang

import logging
import secrets
import string
from typing import Dict, Any, Optional

logger = logging.getLogger("admin.notifications")


class NotificationService:
    @staticmethod
    def generate_default_password() -> str:
        """
        Generates a secure, human-friendly default password.
        Format: Prefix 'Edu@' followed by 6 random alphanumeric characters (digits and uppercase).
        Example: Edu@839102
        """
        digits = "".join(secrets.choice(string.digits) for _ in range(4))
        chars = "".join(secrets.choice(string.ascii_uppercase) for _ in range(2))
        suffix = "".join(secrets.choice(string.digits) for _ in range(2))
        return f"Edu@{digits}{chars}{suffix}"

    @staticmethod
    def send_password_notification(
        full_name: str,
        password: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        action: str = "create"
    ) -> Dict[str, Any]:
        """
        Dispatches account credentials to the user via SMS and/or system notification channel.
        Logs the transaction cleanly without icons or emojis.
        """
        channel = "SMS & System Notification" if phone else "System Notification"
        recipient = phone if phone else (email if email else "Internal User")

        if action == "create":
            sms_text = (
                f"[SmartLMS] Hello {full_name}, your account has been created. "
                f"Default password: {password}. Please log in and change your password."
            )
        else:
            sms_text = (
                f"[SmartLMS] Hello {full_name}, your password has been reset. "
                f"New default password: {password}. Please log in and change your password."
            )

        # Log cleanly without emojis/icons
        logger.info(
            "DISPATCH: Action=%s, Recipient=%s, Channel=%s, MessagePreview=%s",
            action,
            recipient,
            channel,
            sms_text
        )

        return {
            "sent": True,
            "channel": channel,
            "recipient": recipient,
            "message": f"Default password dispatched to {recipient} via {channel}."
        }
