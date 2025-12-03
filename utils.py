#!/usr/bin/env python3
"""
Utility functions for timezone and datetime operations
"""

from datetime import datetime, timezone
from config import WIB_TZ


def utc_to_wib(utc_dt):
    """Convert UTC datetime to WIB (UTC+7)"""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(WIB_TZ)


def get_current_time():
    """Get current time in both UTC and WIB"""
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc.astimezone(WIB_TZ)
    return now_utc, now_wib


def format_time_wib(dt):
    """Format datetime to WIB string"""
    wib_time = utc_to_wib(dt) if dt.tzinfo else dt
    return wib_time.strftime('%Y-%m-%d %H:%M:%S WIB')


def print_separator(char="-", length=60):
    """Print a separator line"""
    print(char * length)


def print_header(text, char="="):
    """Print a header with separators"""
    print_separator(char, 60)
    print(text)
    print_separator(char, 60)