#!/usr/bin/env python3
"""
Telegram to FCM Bridge - STC AutoTrade
Monitors Telegram channel and sends signals to Android app via FCM
"""

import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import Channel
import firebase_admin
from firebase_admin import credentials, messaging

# ============================================================================
# CONFIGURATION
# ============================================================================

# Telegram API credentials - dari environment variables atau default
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '29831238'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '11211a9254f6d1a13f178047bc6ea29a')
TELEGRAM_SESSION = "stc_autotrade_session"
TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID', '-1003193908746'))

# Firebase credentials - prioritas dari environment variable
FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')
FIREBASE_CREDENTIALS_FILE = "service-account.json"

# FCM topic untuk broadcast ke semua devices
FCM_TOPIC = "trading_signals"

# Signal parsing configuration
SIGNAL_PATTERNS = {
    "time_with_trend": re.compile(r'(\d{1,2})[:.:](\d{2})\s*([SB]|SELL|BUY|CALL|PUT)', re.IGNORECASE),
    "simple_trend": re.compile(r'^([SB]|SELL|BUY|CALL|PUT)$', re.IGNORECASE)
}

# ============================================================================
# FIREBASE INITIALIZATION
# ============================================================================

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Cek apakah sudah diinisialisasi
        if firebase_admin._apps:
            print("✅ Firebase already initialized")
            return True
            
        # Prioritas 1: Load dari environment variable (untuk Render)
        if FIREBASE_CREDENTIALS_JSON:
            print("🔧 Loading Firebase credentials from environment variable...")
            cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(cred_dict)
        else:
            # Prioritas 2: Load dari file lokal (untuk development)
            print("🔧 Loading Firebase credentials from file...")
            cred_path = Path(FIREBASE_CREDENTIALS_FILE)
            if not cred_path.exists():
                print(f"❌ Firebase credentials not found: {FIREBASE_CREDENTIALS_FILE}")
                print("📝 Please save your service account JSON as:", FIREBASE_CREDENTIALS_FILE)
                print("   Or set FIREBASE_CREDENTIALS_JSON environment variable")
                return False
            cred = credentials.Certificate(str(cred_path))
            
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False

# ============================================================================
# SIGNAL PARSING
# ============================================================================

def parse_signal(message_text: str) -> dict:
    """
    Parse trading signal from Telegram message
    
    Supported formats:
    - "12:30 S" or "12:30 B" (time with trend)
    - "S" or "B" (simple trend)
    - "SELL" or "BUY" (full words)
    - "CALL" or "PUT" (options style)
    
    Returns:
        dict with keys: trend, has_time, hour, minute, original_message
        or None if no signal detected
    """
    text = message_text.strip().upper()
    
    # Pattern 1: Time specified (HH:MM S/B)
    match = SIGNAL_PATTERNS["time_with_trend"].search(text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        signal = match.group(3)
        
        # Validate time
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
            
        # Determine trend
        if signal in ["S", "SELL", "PUT"]:
            trend = "put"
        elif signal in ["B", "BUY", "CALL"]:
            trend = "call"
        else:
            return None
            
        return {
            "trend": trend,
            "has_time": True,
            "hour": hour,
            "minute": minute,
            "original_message": message_text,
            "parsed_at": datetime.now().isoformat()
        }
    
    # Pattern 2: Simple trend only
    match = SIGNAL_PATTERNS["simple_trend"].match(text)
    if match:
        signal = match.group(1)
        
        if signal in ["S", "SELL", "PUT"]:
            trend = "put"
        elif signal in ["B", "BUY", "CALL"]:
            trend = "call"
        else:
            return None
            
        return {
            "trend": trend,
            "has_time": False,
            "hour": None,
            "minute": None,
            "original_message": message_text,
            "parsed_at": datetime.now().isoformat()
        }
    
    return None

# ============================================================================
# FCM MESSAGING
# ============================================================================

def send_signal_via_fcm(signal_data: dict) -> bool:
    """
    Send trading signal to Android app via FCM
    
    Args:
        signal_data: Parsed signal dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare FCM message
        message = messaging.Message(
            data={
                "type": "TRADING_SIGNAL",
                "trend": signal_data["trend"],
                "has_time": str(signal_data["has_time"]).lower(),
                "hour": str(signal_data.get("hour", "")),
                "minute": str(signal_data.get("minute", "")),
                "original_message": signal_data["original_message"],
                "parsed_at": signal_data["parsed_at"],
                "timestamp": str(int(datetime.now().timestamp() * 1000))
            },
            topic=FCM_TOPIC,
            android=messaging.AndroidConfig(
                priority='high',
                ttl=timedelta(seconds=60),  # Signal expires in 60 seconds
                notification=messaging.AndroidNotification(
                    title="🎯 New Trading Signal",
                    body=f"{signal_data['trend'].upper()}: {signal_data['original_message']}",
                    sound="default",
                    priority="high"
                )
            )
        )
        
        # Send message
        response = messaging.send(message)
        
        print(f"✅ Signal sent via FCM: {response}")
        print(f"   Trend: {signal_data['trend'].upper()}")
        print(f"   Time specified: {signal_data['has_time']}")
        if signal_data['has_time']:
            print(f"   Execute at: {signal_data['hour']:02d}:{signal_data['minute']:02d}")
        
        return True
        
    except Exception as e:
        print(f"❌ FCM send error: {e}")
        return False

# ============================================================================
# TELEGRAM CLIENT
# ============================================================================

async def listen_telegram_signals():
    """Main function to listen for Telegram signals and forward to FCM"""
    
    print("=" * 60)
    print("🚀 TELEGRAM TO FCM BRIDGE - STC AUTOTRADE")
    print("=" * 60)
    
    # Initialize Telegram client
    client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    await client.start()
    print("✅ Telegram client connected")
    
    try:
        # Get channel info
        entity = await client.get_entity(TELEGRAM_CHANNEL_ID)
        print(f"📢 Monitoring channel: {entity.title}")
        print(f"🆔 Channel ID: {entity.id}")
        print(f"📡 FCM Topic: {FCM_TOPIC}")
        print("=" * 60)
        print("🎧 Listening for signals... (Press Ctrl+C to stop)")
        print()
        
        # Register message handler
        @client.on(events.NewMessage(chats=TELEGRAM_CHANNEL_ID))
        async def handle_new_message(event):
            msg = event.message
            
            print("\n" + "-" * 60)
            print(f"📩 New message received")
            print(f"⏰ Time: {msg.date}")
            print(f"📝 Content: {msg.text if msg.text else '[No text]'}")
            
            if not msg.text:
                print("⚠️  Message has no text, skipping")
                return
            
            # Parse signal
            signal = parse_signal(msg.text)
            
            if signal:
                print("✅ Valid signal detected!")
                print(f"   Trend: {signal['trend'].upper()}")
                print(f"   Has time: {signal['has_time']}")
                if signal['has_time']:
                    print(f"   Execute at: {signal['hour']:02d}:{signal['minute']:02d}")
                
                # Send to FCM
                success = send_signal_via_fcm(signal)
                
                if success:
                    print("🎯 Signal forwarded to Android devices")
                else:
                    print("❌ Failed to forward signal")
            else:
                print("ℹ️  Not a trading signal, ignoring")
            
            print("-" * 60)
        
        # Keep running
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping bridge...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("👋 Telegram client disconnected")

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_get_recent_messages(limit=10):
    """Test function to get recent messages from channel"""
    client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    await client.start()
    print("✅ Telegram client connected\n")
    
    try:
        entity = await client.get_entity(TELEGRAM_CHANNEL_ID)
        print(f"📢 Channel: {entity.title}")
        print(f"🆔 ID: {entity.id}")
        print("=" * 60)
        
        messages = await client.get_messages(entity, limit=limit)
        
        print(f"\n📬 Last {len(messages)} messages:\n")
        
        for msg in messages:
            print(f"[{msg.date}] ID: {msg.id}")
            if msg.text:
                print(f"Message: {msg.text[:200]}")
                
                # Try parsing as signal
                signal = parse_signal(msg.text)
                if signal:
                    print(f"✅ Valid signal: {signal['trend'].upper()}")
                    if signal['has_time']:
                        print(f"   Time: {signal['hour']:02d}:{signal['minute']:02d}")
            print("-" * 60)
            
    finally:
        await client.disconnect()

def test_signal_parsing():
    """Test signal parsing with various formats"""
    test_cases = [
        "12:30 S",
        "15:45 B",
        "S",
        "B",
        "SELL",
        "BUY",
        "CALL",
        "PUT",
        "12:30 SELL",
        "Invalid message",
        "Just some random text",
    ]
    
    print("🧪 Testing signal parsing:")
    print("=" * 60)
    
    for test in test_cases:
        result = parse_signal(test)
        status = "✅" if result else "❌"
        print(f"{status} '{test}' -> {result}")
    
    print("=" * 60)

def test_fcm_send():
    """Test FCM message sending"""
    print("🧪 Testing FCM send:")
    print("=" * 60)
    
    # Test signal
    test_signal = {
        "trend": "call",
        "has_time": True,
        "hour": 14,
        "minute": 30,
        "original_message": "14:30 B",
        "parsed_at": datetime.now().isoformat()
    }
    
    success = send_signal_via_fcm(test_signal)
    
    if success:
        print("✅ Test signal sent successfully")
        print("   Check your Android app!")
    else:
        print("❌ Test signal failed")
    
    print("=" * 60)

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    # Deteksi jika running di Render (auto production mode)
    if os.getenv('RENDER'):
        print("\n🔧 Detected Render environment - Starting in production mode\n")
        if not initialize_firebase():
            print("\n❌ Cannot proceed without Firebase")
            exit(1)
        asyncio.run(listen_telegram_signals())
        return
    
    # Interactive mode untuk local development
    print("\n" + "=" * 60)
    print("🤖 TELEGRAM TO FCM BRIDGE - STC AUTOTRADE")
    print("=" * 60)
    print("\nSelect mode:")
    print("1. Start listening for signals (PRODUCTION)")
    print("2. Test: Get recent messages")
    print("3. Test: Signal parsing")
    print("4. Test: Send FCM message")
    print()
    
    choice = input("Enter choice (1/2/3/4): ").strip()
    
    # Initialize Firebase for modes that need it
    if choice in ["1", "4"]:
        if not initialize_firebase():
            print("\n❌ Cannot proceed without Firebase")
            return
    
    if choice == "1":
        # Production mode
        asyncio.run(listen_telegram_signals())
        
    elif choice == "2":
        # Test recent messages
        limit = input("Number of messages (default 10): ").strip()
        limit = int(limit) if limit else 10
        asyncio.run(test_get_recent_messages(limit))
        
    elif choice == "3":
        # Test signal parsing
        test_signal_parsing()
        
    elif choice == "4":
        # Test FCM send
        test_fcm_send()
        
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()