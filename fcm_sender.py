#!/usr/bin/env python3
"""
FCM message sender
"""

from datetime import datetime, timedelta
from firebase_admin import messaging
from config import FCM_TTL_SECONDS, FCM_CHANNEL_ID
from statistics import stats


def send_signal_to_tokens(signal_data: dict, tokens: list) -> dict:
    """
    Send trading signal to specified FCM tokens
    
    Args:
        signal_data: Signal data dict
        tokens: List of tuples [(identifier, fcmToken, type), ...]
    
    Returns:
        dict with success/failure counts
    """
    try:
        print("=" * 60)
        print(f"🚀 SENDING FCM TO {len(tokens)} TOKENS")
        print("=" * 60)
        
        # Validate signal data
        if not signal_data.get('has_time'):
            print("❌ ERROR: Signal has no time!")
            return {"success": 0, "failed": 0, "total": 0, "user_success": 0, "admin_success": 0}
            
        hour = signal_data.get('hour')
        minute = signal_data.get('minute')
        second = signal_data.get('second', 0)  # Default 0 jika tidak ada
        
        if hour is None or minute is None or not isinstance(hour, int) or not isinstance(minute, int):
            print(f"❌ ERROR: Invalid hour/minute!")
            return {"success": 0, "failed": 0, "total": 0, "user_success": 0, "admin_success": 0}
        
        if not tokens:
            print("⚠️  No FCM tokens provided")
            return {"success": 0, "failed": 0, "total": 0, "user_success": 0, "admin_success": 0}
        
        print(f"📡 Sending to {len(tokens)} devices...")
        
        # Prepare FCM data
        trend_letter = "B" if signal_data['trend'] == "call" else "S"
        formatted_message = f"{hour:02d}:{minute:02d}:{second:02d} {trend_letter}"
        
        fcm_data = {
            "type": "TRADING_SIGNAL",
            "trend": signal_data["trend"],
            "has_time": "true",
            "hour": str(hour),
            "minute": str(minute),
            "second": str(second),
            "original_message": signal_data["original_message"],
            "formatted_message": formatted_message,
            "auto_time_added": str(signal_data.get("auto_time_added", False)).lower(),
            "parsed_at": signal_data["parsed_at"],
            "timestamp": str(int(datetime.now().timestamp() * 1000))
        }
        
        # Send to each token
        success_count = 0
        failed_count = 0
        user_success = 0
        admin_success = 0
        
        for identifier, token, user_type in tokens:
            try:
                message = messaging.Message(
                    data=fcm_data,
                    token=token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        ttl=timedelta(seconds=FCM_TTL_SECONDS),
                        notification=messaging.AndroidNotification(
                            title="🎯 New Trading Signal",
                            body=formatted_message,
                            sound="default",
                            priority="high",
                            channel_id=FCM_CHANNEL_ID
                        )
                    )
                )
                
                response = messaging.send(message)
                success_count += 1
                
                if "admin" in user_type.lower():
                    admin_success += 1
                else:
                    user_success += 1
                
                print(f"   ✅ Sent to {identifier} ({user_type}): {response}")
                stats.log_signal(signal_data["trend"], True, identifier, user_type)
                
            except messaging.UnregisteredError:
                failed_count += 1
                print(f"   ❌ Invalid token for {identifier} ({user_type})")
                stats.log_signal(signal_data["trend"], False, identifier, user_type)
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Failed to send to {identifier} ({user_type}): {e}")
                stats.log_signal(signal_data["trend"], False, identifier, user_type)
        
        print(f"\n📊 Send Summary:")
        print(f"   Total: {len(tokens)}")
        print(f"   Success: {success_count}")
        print(f"   - Users: {user_success}")
        print(f"   - Admins: {admin_success}")
        print(f"   Failed: {failed_count}")
        print("=" * 60)
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(tokens),
            "user_success": user_success,
            "admin_success": admin_success
        }
        
    except Exception as e:
        print(f"❌ Error in send_signal_to_tokens: {e}")
        import traceback
        traceback.print_exc()
        return {"success": 0, "failed": 0, "total": 0, "user_success": 0, "admin_success": 0}