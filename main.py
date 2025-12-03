#!/usr/bin/env python3
"""
Main entry point for Telegram to FCM Bridge
"""

import os
import asyncio
from datetime import datetime
from utils import get_current_time, print_header
from firebase_manager import firebase_manager
from telegram_client import listen_telegram_signals
from fcm_sender import send_signal_to_tokens
from migrations import (
    migrate_add_fcm_field_all,
    migrate_add_fcm_field_to_users,
    migrate_add_fcm_field_to_admins,
    check_fcm_token_status,
    custom_migration
)


def test_view_all_tokens():
    """View all FCM tokens (users + admins)"""
    print_header("🧪 VIEWING ALL FCM TOKENS")
    
    tokens = firebase_manager.get_all_fcm_tokens_combined()
    
    print(f"\n📊 Summary:")
    print(f"   Total tokens: {len(tokens)}")
    
    if tokens:
        user_count = sum(1 for _, _, t in tokens if t == 'user')
        admin_count = sum(1 for _, _, t in tokens if 'admin' in t.lower())
        
        print(f"   Users: {user_count}")
        print(f"   Admins: {admin_count}")
        
        print(f"\n📱 All Devices:")
        for identifier, token, user_type in tokens:
            print(f"   • {identifier} ({user_type})")
            print(f"     Token: {token[:30]}...{token[-20:]}")
    else:
        print("\n⚠️  No active FCM tokens found")
        print("\n💡 Possible reasons:")
        print("   1. Users/admins don't have fcmToken field")
        print("   2. Users/admins haven't logged in to app yet")
        print("   3. All users/admins are inactive")
    
    print("=" * 60)


def test_send_to_users():
    """Test sending signal to users only"""
    print_header("🧪 TESTING SEND TO USERS ONLY")
    
    now_utc, now_wib = get_current_time()
    
    test_signal = {
        "trend": "call",
        "has_time": True,
        "hour": now_wib.hour,
        "minute": (now_wib.minute + 1) % 60,
        "original_message": f"TEST USER: {now_wib.hour:02d}:{(now_wib.minute + 1) % 60:02d} B",
        "auto_time_added": False,
        "parsed_at": datetime.now().isoformat()
    }
    
    tokens = firebase_manager.get_all_fcm_tokens_combined(user_only=True)
    result = send_signal_to_tokens(test_signal, tokens)
    
    print(f"\n✅ Test completed!")
    print(f"   Total: {result['total']}")
    print(f"   Success: {result['success']}")
    print(f"   Failed: {result['failed']}")
    print("=" * 60)


def test_send_to_admins():
    """Test sending signal to admins only"""
    print_header("🧪 TESTING SEND TO ADMINS ONLY")
    
    now_utc, now_wib = get_current_time()
    
    test_signal = {
        "trend": "put",
        "has_time": True,
        "hour": now_wib.hour,
        "minute": (now_wib.minute + 1) % 60,
        "original_message": f"TEST ADMIN: {now_wib.hour:02d}:{(now_wib.minute + 1) % 60:02d} S",
        "auto_time_added": False,
        "parsed_at": datetime.now().isoformat()
    }
    
    tokens = firebase_manager.get_all_fcm_tokens_combined(admin_only=True)
    result = send_signal_to_tokens(test_signal, tokens)
    
    print(f"\n✅ Test completed!")
    print(f"   Total: {result['total']}")
    print(f"   Success: {result['success']}")
    print(f"   Failed: {result['failed']}")
    print("=" * 60)


def test_send_to_super_admin():
    """Test sending signal to super admin only"""
    print_header("🧪 TESTING SEND TO SUPER ADMIN ONLY")
    
    now_utc, now_wib = get_current_time()
    
    test_signal = {
        "trend": "call",
        "has_time": True,
        "hour": now_wib.hour,
        "minute": (now_wib.minute + 1) % 60,
        "original_message": f"TEST SUPER ADMIN: {now_wib.hour:02d}:{(now_wib.minute + 1) % 60:02d} B",
        "auto_time_added": False,
        "parsed_at": datetime.now().isoformat()
    }
    
    tokens = firebase_manager.get_all_fcm_tokens_combined(admin_only=True, admin_role_filter='super_admin')
    result = send_signal_to_tokens(test_signal, tokens)
    
    print(f"\n✅ Test completed!")
    print(f"   Total: {result['total']}")
    print(f"   Success: {result['success']}")
    print(f"   Failed: {result['failed']}")
    print("=" * 60)


def test_send_to_all():
    """Test sending signal to all (users + admins)"""
    print_header("🧪 TESTING SEND TO ALL (USERS + ADMINS)")
    
    now_utc, now_wib = get_current_time()
    
    test_signal = {
        "trend": "call",
        "has_time": True,
        "hour": now_wib.hour,
        "minute": (now_wib.minute + 1) % 60,
        "original_message": f"TEST ALL: {now_wib.hour:02d}:{(now_wib.minute + 1) % 60:02d} B",
        "auto_time_added": False,
        "parsed_at": datetime.now().isoformat()
    }
    
    tokens = firebase_manager.get_all_fcm_tokens_combined()
    result = send_signal_to_tokens(test_signal, tokens)
    
    print(f"\n✅ Test completed!")
    print(f"   Total: {result['total']}")
    print(f"   Success: {result['success']}")
    print(f"   - Users: {result['user_success']}")
    print(f"   - Admins: {result['admin_success']}")
    print(f"   Failed: {result['failed']}")
    print("=" * 60)


def show_menu():
    """Display main menu"""
    print_header("🤖 TELEGRAM TO FCM BRIDGE", "=")
    print("\n📡 PRODUCTION MODES:")
    print("1. 🚀 Production: All Users + All Admins (Realtime)")
    print("2. 🧪 Test: Admins Only (Realtime)")
    print("3. 🧪 Test: Super Admin Only (Realtime)")
    print("4. 🧪 Test: Users Only (Realtime)")
    
    print("\n🧪 TESTING MODES:")
    print("5. 📤 Send Test Signal: All Users + All Admins")
    print("6. 📤 Send Test Signal: Admins Only")
    print("7. 📤 Send Test Signal: Super Admin Only")
    print("8. 📤 Send Test Signal: Users Only")
    
    print("\n📊 INFORMATION:")
    print("9. 📋 View All FCM Tokens (Users + Admins)")
    print("10. 🔍 Check FCM Token Status")
    
    print("\n🔧 MIGRATIONS:")
    print("11. 🔄 Add fcmToken Field: All (Users + Admins)")
    print("12. 🔄 Add fcmToken Field: Users Only")
    print("13. 🔄 Add fcmToken Field: Admins Only")
    print("14. ⚡ Custom Migration")
    
    print("\n0. 🚪 Exit")
    print("=" * 60)


def main():
    """Main entry point"""
    
    # Initialize Firebase
    if not firebase_manager.initialize():
        print("\n❌ Cannot proceed without Firebase")
        exit(1)
    
    # Check if running on Render (production)
    if os.getenv('RENDER'):
        print("\n🔧 Detected Render environment - Starting production mode")
        print("📡 Mode: All Users + All Admins\n")
        asyncio.run(listen_telegram_signals())
        return
    
    # Local development menu
    while True:
        show_menu()
        choice = input("Enter choice: ").strip()
        print()
        
        if choice == "1":
            # Production: All Users + All Admins
            asyncio.run(listen_telegram_signals())
            
        elif choice == "2":
            # Test: Admins Only
            asyncio.run(listen_telegram_signals(admin_only=True))
            
        elif choice == "3":
            # Test: Super Admin Only
            asyncio.run(listen_telegram_signals(admin_only=True, admin_role_filter='super_admin'))
            
        elif choice == "4":
            # Test: Users Only
            asyncio.run(listen_telegram_signals(user_only=True))
            
        elif choice == "5":
            # Send Test: All
            test_send_to_all()
            input("\nPress Enter to continue...")
            
        elif choice == "6":
            # Send Test: Admins Only
            test_send_to_admins()
            input("\nPress Enter to continue...")
            
        elif choice == "7":
            # Send Test: Super Admin Only
            test_send_to_super_admin()
            input("\nPress Enter to continue...")
            
        elif choice == "8":
            # Send Test: Users Only
            test_send_to_users()
            input("\nPress Enter to continue...")
            
        elif choice == "9":
            # View All Tokens
            test_view_all_tokens()
            input("\nPress Enter to continue...")
            
        elif choice == "10":
            # Check FCM Token Status
            check_fcm_token_status()
            input("\nPress Enter to continue...")
            
        elif choice == "11":
            # Migration: All
            print("⚠️  WARNING: This will modify your Firestore database!")
            print("This will add 'fcmToken' and 'fcmTokenUpdatedAt' fields to users and admins.")
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                migrate_add_fcm_field_all()
            else:
                print("❌ Migration cancelled")
            input("\nPress Enter to continue...")
            
        elif choice == "12":
            # Migration: Users Only
            print("⚠️  WARNING: This will modify your Firestore database!")
            print("This will add 'fcmToken' and 'fcmTokenUpdatedAt' fields to users.")
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                migrate_add_fcm_field_to_users()
            else:
                print("❌ Migration cancelled")
            input("\nPress Enter to continue...")
            
        elif choice == "13":
            # Migration: Admins Only
            print("⚠️  WARNING: This will modify your Firestore database!")
            print("This will add 'fcmToken' and 'fcmTokenUpdatedAt' fields to admins.")
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                migrate_add_fcm_field_to_admins()
            else:
                print("❌ Migration cancelled")
            input("\nPress Enter to continue...")
            
        elif choice == "14":
            # Custom Migration
            print("⚠️  WARNING: This will run custom migration!")
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                custom_migration()
            else:
                print("❌ Custom migration cancelled")
            input("\nPress Enter to continue...")
            
        elif choice == "0":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice!")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()