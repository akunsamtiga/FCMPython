#!/usr/bin/env python3
"""
Firebase and Firestore management
"""

import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CREDENTIALS_JSON, FIREBASE_CREDENTIALS_FILE


class FirebaseManager:
    def __init__(self):
        self.db = None
    
    def initialize(self):
        """Initialize Firebase Admin SDK with Firestore"""
        try:
            if firebase_admin._apps:
                print("✅ Firebase already initialized")
                self.db = firestore.client()
                return True
                
            if FIREBASE_CREDENTIALS_JSON:
                print("🔧 Loading Firebase credentials from environment variable...")
                cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
                cred = credentials.Certificate(cred_dict)
            else:
                print("🔧 Loading Firebase credentials from file...")
                cred_path = Path(FIREBASE_CREDENTIALS_FILE)
                if not cred_path.exists():
                    print(f"❌ Firebase credentials not found: {FIREBASE_CREDENTIALS_FILE}")
                    return False
                cred = credentials.Certificate(str(cred_path))
                
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            
            print("✅ Firebase initialized successfully")
            print("✅ Firestore client ready")
            return True
            
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            return False
    
    def get_all_active_user_fcm_tokens(self) -> list:
        """
        Get all active FCM tokens from whitelist_users collection
        
        Returns:
            list of tuples: [(userId, fcmToken, email), ...]
        """
        try:
            if self.db is None:
                print("❌ Firestore client not initialized")
                return []
            
            print("🔍 Fetching active user FCM tokens from Firestore...")
            
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            users_ref = self.db.collection('whitelist_users')
            query = users_ref.where(
                filter=FieldFilter('isActive', '==', True)
            ).stream()
            
            tokens = []
            processed_count = 0
            
            for doc in query:
                processed_count += 1
                user_data = doc.to_dict()
                user_id = user_data.get('userId', '')
                fcm_token = user_data.get('fcmToken', '')
                email = user_data.get('email', '')
                
                if fcm_token and fcm_token.strip():
                    tokens.append((user_id, fcm_token, email))
                    print(f"   ✅ {email}: Token {fcm_token[:20]}...{fcm_token[-20:]}")
                else:
                    print(f"   ⚠️  {email}: No FCM token (skipped)")
            
            print(f"📊 Processed {processed_count} active users")
            print(f"📊 Found {len(tokens)} users with valid FCM tokens")
            return tokens
            
        except Exception as e:
            print(f"❌ Error fetching user FCM tokens: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_admin_fcm_tokens(self, role_filter=None) -> list:
        """
        Get all active admin FCM tokens from admin_users collection
        
        Args:
            role_filter: Optional role filter ('admin', 'super_admin', etc.)
        
        Returns:
            list of tuples: [(email, fcmToken, role), ...]
        """
        try:
            if self.db is None:
                print("❌ Firestore client not initialized")
                return []
            
            print("🔍 Fetching admin FCM tokens from Firestore...")
            
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            admins_ref = self.db.collection('admin_users')
            query = admins_ref.where(
                filter=FieldFilter('isActive', '==', True)
            ).stream()
            
            tokens = []
            processed_count = 0
            
            for doc in query:
                processed_count += 1
                admin_data = doc.to_dict()
                email = admin_data.get('email', '')
                fcm_token = admin_data.get('fcmToken', '')
                role = admin_data.get('role', 'admin')
                
                # Apply role filter if specified
                if role_filter and role != role_filter:
                    continue
                
                if fcm_token and fcm_token.strip():
                    tokens.append((email, fcm_token, role))
                    print(f"   ✅ {email} ({role}): Token {fcm_token[:20]}...{fcm_token[-20:]}")
                else:
                    print(f"   ⚠️  {email} ({role}): No FCM token (skipped)")
            
            print(f"📊 Processed {processed_count} active admins")
            print(f"📊 Found {len(tokens)} admins with valid FCM tokens")
            return tokens
            
        except Exception as e:
            print(f"❌ Error fetching admin FCM tokens: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_all_fcm_tokens_combined(self, user_only=False, admin_only=False, admin_role_filter=None) -> list:
        """
        Get FCM tokens from whitelist users and/or admins
        
        Args:
            user_only: If True, only get user tokens
            admin_only: If True, only get admin tokens
            admin_role_filter: Filter admins by role
        
        Returns:
            list of tuples: [(identifier, fcmToken, type), ...]
        """
        try:
            print("=" * 60)
            
            if user_only:
                print("🔍 FETCHING USER FCM TOKENS ONLY")
            elif admin_only:
                print("🔍 FETCHING ADMIN FCM TOKENS ONLY")
            else:
                print("🔍 FETCHING ALL FCM TOKENS (USERS + ADMINS)")
            
            print("=" * 60)
            
            all_tokens = []
            
            # Get users
            if not admin_only:
                print("\n📱 Fetching whitelist users...")
                user_tokens = self.get_all_active_user_fcm_tokens()
                for user_id, token, email in user_tokens:
                    all_tokens.append((email, token, 'user'))
                print(f"   Found {len(user_tokens)} users with tokens")
            
            # Get admins
            if not user_only:
                print("\n👑 Fetching admins...")
                admin_tokens = self.get_all_admin_fcm_tokens(role_filter=admin_role_filter)
                for email, token, role in admin_tokens:
                    all_tokens.append((email, token, f'admin ({role})'))
                print(f"   Found {len(admin_tokens)} admins with tokens")
            
            print(f"\n📊 TOTAL: {len(all_tokens)} devices with FCM tokens")
            print("=" * 60)
            
            return all_tokens
            
        except Exception as e:
            print(f"❌ Error fetching combined tokens: {e}")
            import traceback
            traceback.print_exc()
            return []


# Global Firebase manager instance
firebase_manager = FirebaseManager()