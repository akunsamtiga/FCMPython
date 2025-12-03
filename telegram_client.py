#!/usr/bin/env python3
"""
Telegram client for monitoring signals
"""

import asyncio
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, 
    TimedOutError,
    AuthKeyUnregisteredError,
    ServerError,
    RPCError
)
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION, TELEGRAM_CHANNEL_ID
from utils import get_current_time, utc_to_wib, print_separator
from signal_parser import parse_signal
from fcm_sender import send_signal_to_tokens
from firebase_manager import firebase_manager
from statistics import stats


async def listen_telegram_signals(user_only=False, admin_only=False, admin_role_filter=None):
    """
    Listen for Telegram signals and broadcast via FCM with auto-reconnect
    
    Args:
        user_only: If True, send only to users
        admin_only: If True, send only to admins
        admin_role_filter: Filter admins by role (e.g., 'super_admin')
    """
    
    mode_text = "ALL USERS + ADMINS"
    if user_only:
        mode_text = "USERS ONLY"
    elif admin_only:
        if admin_role_filter:
            mode_text = f"ADMINS ONLY ({admin_role_filter.upper()})"
        else:
            mode_text = "ADMINS ONLY (ALL ROLES)"
    
    max_retries = 10  # Increased for production stability
    retry_delay = 5  # seconds
    retry_count = 0
    client = None
    
    while True:
        try:
            print("=" * 60)
            print(f"🚀 TELEGRAM TO FCM BRIDGE - {mode_text}")
            if retry_count > 0:
                print(f"🔄 Reconnection attempt {retry_count}/{max_retries}")
            print("=" * 60)
            
            now_utc, now_wib = get_current_time()
            print(f"⏰ Current UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"🇮🇩 Current WIB: {now_wib.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"📡 Method: Token-based (Firestore)")
            print(f"👥 Target: {mode_text}")
            print()
            
            # Create new client instance
            client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_API_ID, TELEGRAM_API_HASH)
            
            # Set connection timeout
            client.flood_sleep_threshold = 60
            
            await client.start()
            print("✅ Telegram client connected")
            retry_count = 0  # Reset retry count on successful connection
            retry_delay = 5  # Reset retry delay
            
            try:
                entity = await client.get_entity(TELEGRAM_CHANNEL_ID)
                print(f"📢 Monitoring channel: {entity.title}")
                print(f"🆔 Channel ID: {entity.id}")
                print("=" * 60)
                print("🎧 Listening for signals... (Press Ctrl+C to stop)")
                print()
                
                @client.on(events.NewMessage(chats=TELEGRAM_CHANNEL_ID))
                async def handle_new_message(event):
                    try:
                        msg = event.message
                        
                        utc_time = msg.date
                        wib_time = utc_to_wib(utc_time)
                        
                        print("\n" + "-" * 60)
                        print(f"📩 New message received")
                        print(f"⏰ WIB: {wib_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"📝 Content: {msg.text if msg.text else '[No text]'}")
                        
                        if not msg.text:
                            print("⚠️ Message has no text, skipping")
                            return
                        
                        # Parse signal
                        signal = parse_signal(msg.text, message_time=msg.date)
                        
                        if signal:
                            print("✅ Valid signal detected!")
                            print(f"   Trend: {signal['trend'].upper()}")
                            print(f"   Execute at: {signal['hour']:02d}:{signal['minute']:02d} WIB")
                            
                            # Get tokens based on mode
                            tokens = firebase_manager.get_all_fcm_tokens_combined(
                                user_only=user_only,
                                admin_only=admin_only,
                                admin_role_filter=admin_role_filter
                            )
                            
                            # Send to tokens
                            result = send_signal_to_tokens(signal, tokens)
                            
                            print(f"📊 Current Statistics: {stats.get_summary()}")
                        else:
                            print("ℹ️ Not a trading signal, ignoring")
                        
                        print_separator()
                        
                    except Exception as e:
                        print(f"❌ Error handling message: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Keep connection alive
                await client.run_until_disconnected()
                
            except KeyboardInterrupt:
                raise  # Re-raise to outer handler
                
            except FloodWaitError as e:
                print(f"⚠️ Flood wait error: Need to wait {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                raise  # Trigger reconnection after wait
                
            except TimedOutError as e:
                print(f"⚠️ Timeout error: {e}")
                raise  # Trigger reconnection
                
            except ServerError as e:
                print(f"⚠️ Server error: {e}")
                raise  # Trigger reconnection
                
            except AuthKeyUnregisteredError:
                print("❌ Auth key unregistered. Please delete session file and restart.")
                break  # Exit completely
                
            except OSError as e:
                print(f"⚠️ Network/OS error: {e}")
                raise  # Trigger reconnection
                
            except Exception as e:
                print(f"❌ Unexpected error in main loop: {e}")
                import traceback
                traceback.print_exc()
                raise  # Trigger reconnection
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping bridge...")
            stats.print_summary()
            
            # Clean disconnect
            if client and client.is_connected():
                try:
                    await client.disconnect()
                    print("👋 Telegram client disconnected")
                except:
                    pass
            
            break  # Exit the retry loop completely
            
        except Exception as e:
            retry_count += 1
            print(f"\n❌ Connection error: {e}")
            
            # Clean disconnect before retry
            if client:
                try:
                    if client.is_connected():
                        await client.disconnect()
                        print("🔌 Disconnected previous session")
                except Exception as disc_error:
                    print(f"⚠️ Error during disconnect: {disc_error}")
            
            if retry_count >= max_retries:
                print(f"❌ Max retries ({max_retries}) reached. Exiting...")
                stats.print_summary()
                break
            
            print(f"\n🔄 Reconnecting in {retry_delay} seconds...")
            print(f"   Attempt {retry_count}/{max_retries}")
            
            await asyncio.sleep(retry_delay)
            
            # Exponential backoff with max cap
            retry_delay = min(retry_delay * 1.5, 60)  # Max 60 seconds