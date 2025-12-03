#!/usr/bin/env python3
"""
Configuration file for Telegram to FCM Bridge
"""

import os
import re
from datetime import timedelta, timezone

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '29831238'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '11211a9254f6d1a13f178047bc6ea29a')
TELEGRAM_SESSION = "stc_autotrade_session"
TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID', '-1003193908746'))

# ============================================================================
# FIREBASE CONFIGURATION
# ============================================================================

FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')
FIREBASE_CREDENTIALS_FILE = "service-account.json"

# ============================================================================
# TIMEZONE CONFIGURATION
# ============================================================================

WIB_TZ = timezone(timedelta(hours=7))

# ============================================================================
# SIGNAL PATTERNS
# ============================================================================

SIGNAL_PATTERNS = {
    "time_with_trend": re.compile(
        r'(\d{1,2})[:\.]\s*(\d{2})\s+([SB])', 
        re.IGNORECASE
    ),
    "time_with_trend_strict": re.compile(
        r'(\d{1,2})[:\.](\d{2})\s+([SB])', 
        re.IGNORECASE
    ),
    "simple_trend": re.compile(r'^([SB])$', re.IGNORECASE)
}

# ============================================================================
# FCM CONFIGURATION
# ============================================================================

FCM_TTL_SECONDS = 60
FCM_CHANNEL_ID = "trading_signals"