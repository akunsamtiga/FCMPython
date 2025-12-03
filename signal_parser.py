#!/usr/bin/env python3
"""
Trading signal parser with smart execution timing
"""

from datetime import datetime
from config import SIGNAL_PATTERNS
from utils import utc_to_wib


def parse_signal(message_text: str, message_time: datetime = None) -> dict:
    """Parse trading signal from Telegram message"""
    text = message_text.strip().upper()
    
    print(f"🔍 Parsing signal:")
    print(f"   Input: '{text}'")
    
    # Get current WIB time for seconds
    current_wib = None
    if message_time:
        current_wib = utc_to_wib(message_time)
    
    # Check if message contains multiple signals
    all_matches = SIGNAL_PATTERNS["time_with_trend"].findall(text)
    
    if len(all_matches) > 1:
        print("⚠️  Multiple signals detected - IGNORING")
        return None
    
    # Pattern 1: Time specified
    match = SIGNAL_PATTERNS["time_with_trend"].search(text)
    
    if not match:
        match = SIGNAL_PATTERNS["time_with_trend_strict"].search(text)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        signal = match.group(3)
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            print(f"⚠️  Invalid time: {hour}:{minute}")
            return None
        
        trend = "put" if signal == "S" else "call"
        
        # Get seconds from message time
        second = current_wib.second if current_wib else 0
        
        print(f"✅ Parsed: {hour:02d}:{minute:02d}:{second:02d} {trend.upper()}")
        
        return {
            "trend": trend,
            "has_time": True,
            "hour": hour,
            "minute": minute,
            "second": second,
            "original_message": message_text,
            "auto_time_added": False,
            "parsed_at": datetime.now().isoformat()
        }
    
    # Pattern 2: Simple trend only with smart execution timing
    match = SIGNAL_PATTERNS["simple_trend"].match(text)
    if match:
        signal = match.group(1)
        trend = "put" if signal == "S" else "call"
        
        if current_wib:
            # Calculate seconds until next minute boundary
            seconds_in_current_minute = current_wib.second
            seconds_until_next_minute = 60 - seconds_in_current_minute
            
            # Determine execution time based on 30-second threshold
            if seconds_until_next_minute >= 30:
                # Execute at next minute (e.g., 15:20:28 -> 15:21:00)
                execution_minute = (current_wib.minute + 1) % 60
                execution_hour = current_wib.hour + (1 if current_wib.minute == 59 else 0)
                execution_hour = execution_hour % 24
                execution_second = 0  # Start at 0 seconds
                print(f"🕐 Signal received at :{seconds_in_current_minute}s → {seconds_until_next_minute}s remaining → Execute NEXT minute")
            else:
                # Execute 2 minutes later (e.g., 15:20:32 -> 15:22:00)
                execution_minute = (current_wib.minute + 2) % 60
                execution_hour = current_wib.hour + ((current_wib.minute + 2) // 60)
                execution_hour = execution_hour % 24
                execution_second = 0  # Start at 0 seconds
                print(f"🕐 Signal received at :{seconds_in_current_minute}s → {seconds_until_next_minute}s remaining → Execute SKIP to +2 minutes")
            
            hour = execution_hour
            minute = execution_minute
            second = execution_second
            
            print(f"✅ Auto-time: {hour:02d}:{minute:02d}:{second:02d} WIB (from {current_wib.strftime('%H:%M:%S')})")
            
            return {
                "trend": trend,
                "has_time": True,
                "hour": hour,
                "minute": minute,
                "second": second,
                "original_message": message_text,
                "auto_time_added": True,
                "parsed_at": datetime.now().isoformat()
            }
    
    print(f"❌ No valid signal pattern found")
    return None