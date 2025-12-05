#!/usr/bin/env python3
"""
Database migration functions
"""

from firebase_manager import firebase_manager


def migrate_add_fcm_field_to_users():
    """
    Migration: Add fcmToken and fcmTokenUpdatedAt fields to whitelist_users
    """
    try:
        if firebase_manager.db is None:
            print("❌ Firestore client not initialized")
            return False
        
        print("=" * 60)
        print("🔧 MIGRATION: Adding fcmToken field to users")
        print("=" * 60)
        
        users_ref = firebase_manager.db.collection('whitelist_users')
        all_users = users_ref.stream()
        
        updated_count = 0
        skipped_count = 0
        
        for doc in all_users:
            user_data = doc.to_dict()
            email = user_data.get('email', 'unknown')
            
            if 'fcmToken' in user_data:
                print(f"   ⏭️  {email}: Already has fcmToken field (skipped)")
                skipped_count += 1
                continue
            
            doc.reference.update({
                'fcmToken': '',
                'fcmTokenUpdatedAt': 0
            })
            
            updated_count += 1
            print(f"   ✅ {email}: Added fcmToken field")
        
        print(f"\n📊 Migration Summary:")
        print(f"   Updated: {updated_count} users")
        print(f"   Skipped: {skipped_count} users (already have field)")
        print(f"   Total: {updated_count + skipped_count} users")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_add_fcm_field_to_admins():
    """
    Migration: Add fcmToken and fcmTokenUpdatedAt fields to admin_users
    """
    try:
        if firebase_manager.db is None:
            print("❌ Firestore client not initialized")
            return False
        
        print("=" * 60)
        print("🔧 MIGRATION: Adding fcmToken field to admins")
        print("=" * 60)
        
        admins_ref = firebase_manager.db.collection('admin_users')
        all_admins = admins_ref.stream()
        
        updated_count = 0
        skipped_count = 0
        
        for doc in all_admins:
            admin_data = doc.to_dict()
            email = admin_data.get('email', 'unknown')
            
            if 'fcmToken' in admin_data:
                print(f"   ⏭️  {email}: Already has fcmToken field (skipped)")
                skipped_count += 1
                continue
            
            doc.reference.update({
                'fcmToken': '',
                'fcmTokenUpdatedAt': 0
            })
            
            updated_count += 1
            print(f"   ✅ {email}: Added fcmToken field")
        
        print(f"\n📊 Migration Summary:")
        print(f"   Updated: {updated_count} admins")
        print(f"   Skipped: {skipped_count} admins (already have field)")
        print(f"   Total: {updated_count + skipped_count} admins")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_add_fcm_field_all():
    """
    Migration: Add fcmToken field to both users and admins
    """
    print("🔧 Running migration for USERS and ADMINS...\n")
    
    success_users = migrate_add_fcm_field_to_users()
    print()
    success_admins = migrate_add_fcm_field_to_admins()
    
    if success_users and success_admins:
        print("\n✅ Migration completed successfully for both collections!")
        return True
    else:
        print("\n⚠️  Migration completed with some errors")
        return False


def reset_fcm_token_for_users(reset_all=False):
    """
    Reset FCM token for whitelist_users
    
    Args:
        reset_all: If True, reset all users. If False, ask for specific email
    """
    try:
        if firebase_manager.db is None:
            print("❌ Firestore client not initialized")
            return False
        
        print("=" * 60)
        print("🔄 RESET FCM TOKEN: Users")
        print("=" * 60)
        
        users_ref = firebase_manager.db.collection('whitelist_users')
        
        if reset_all:
            print("\n⚠️  WARNING: This will reset ALL user FCM tokens!")
            confirm = input("Type 'yes' to confirm: ").strip().lower()
            if confirm != 'yes':
                print("❌ Reset cancelled")
                return False
            
            all_users = users_ref.stream()
            reset_count = 0
            
            for doc in all_users:
                user_data = doc.to_dict()
                email = user_data.get('email', 'unknown')
                
                doc.reference.update({
                    'fcmToken': '',
                    'fcmTokenUpdatedAt': 0
                })
                
                reset_count += 1
                print(f"   ✅ {email}: FCM token reset")
            
            print(f"\n📊 Reset Summary:")
            print(f"   Total users reset: {reset_count}")
            
        else:
            email_to_reset = input("\nEnter user email to reset: ").strip()
            if not email_to_reset:
                print("❌ Email cannot be empty")
                return False
            
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            query = users_ref.where(
                filter=FieldFilter('email', '==', email_to_reset)
            ).limit(1).stream()
            
            found = False
            for doc in query:
                found = True
                user_data = doc.to_dict()
                
                doc.reference.update({
                    'fcmToken': '',
                    'fcmTokenUpdatedAt': 0
                })
                
                print(f"\n✅ FCM token reset for: {email_to_reset}")
                print(f"   Previous token: {user_data.get('fcmToken', 'N/A')[:30]}...")
                print(f"   New token: (empty)")
            
            if not found:
                print(f"\n❌ User not found: {email_to_reset}")
                return False
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Reset error: {e}")
        import traceback
        traceback.print_exc()
        return False


def reset_fcm_token_for_admins(reset_all=False, role_filter=None):
    """
    Reset FCM token for admin_users
    
    Args:
        reset_all: If True, reset all admins. If False, ask for specific email
        role_filter: Optional role filter ('admin', 'super_admin', etc.)
    """
    try:
        if firebase_manager.db is None:
            print("❌ Firestore client not initialized")
            return False
        
        print("=" * 60)
        print("🔄 RESET FCM TOKEN: Admins")
        print("=" * 60)
        
        admins_ref = firebase_manager.db.collection('admin_users')
        
        if reset_all:
            role_text = f" ({role_filter.upper()})" if role_filter else ""
            print(f"\n⚠️  WARNING: This will reset ALL admin{role_text} FCM tokens!")
            confirm = input("Type 'yes' to confirm: ").strip().lower()
            if confirm != 'yes':
                print("❌ Reset cancelled")
                return False
            
            all_admins = admins_ref.stream()
            reset_count = 0
            
            for doc in all_admins:
                admin_data = doc.to_dict()
                email = admin_data.get('email', 'unknown')
                role = admin_data.get('role', 'admin')
                
                # Apply role filter if specified
                if role_filter and role != role_filter:
                    continue
                
                doc.reference.update({
                    'fcmToken': '',
                    'fcmTokenUpdatedAt': 0
                })
                
                reset_count += 1
                print(f"   ✅ {email} ({role}): FCM token reset")
            
            print(f"\n📊 Reset Summary:")
            print(f"   Total admins reset: {reset_count}")
            
        else:
            email_to_reset = input("\nEnter admin email to reset: ").strip()
            if not email_to_reset:
                print("❌ Email cannot be empty")
                return False
            
            from google.cloud.firestore_v1.base_query import FieldFilter
            
            query = admins_ref.where(
                filter=FieldFilter('email', '==', email_to_reset)
            ).limit(1).stream()
            
            found = False
            for doc in query:
                found = True
                admin_data = doc.to_dict()
                role = admin_data.get('role', 'admin')
                
                doc.reference.update({
                    'fcmToken': '',
                    'fcmTokenUpdatedAt': 0
                })
                
                print(f"\n✅ FCM token reset for: {email_to_reset} ({role})")
                print(f"   Previous token: {admin_data.get('fcmToken', 'N/A')[:30]}...")
                print(f"   New token: (empty)")
            
            if not found:
                print(f"\n❌ Admin not found: {email_to_reset}")
                return False
        
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Reset error: {e}")
        import traceback
        traceback.print_exc()
        return False


def reset_fcm_token_all(reset_all_users=False, reset_all_admins=False, admin_role_filter=None):
    """
    Reset FCM tokens for both users and admins
    
    Args:
        reset_all_users: If True, reset all users
        reset_all_admins: If True, reset all admins
        admin_role_filter: Filter admins by role
    """
    print("=" * 60)
    print("🔄 RESET FCM TOKENS: Users + Admins")
    print("=" * 60)
    
    success_users = False
    success_admins = False
    
    if reset_all_users:
        print("\n👥 Resetting user FCM tokens...")
        success_users = reset_fcm_token_for_users(reset_all=True)
    
    if reset_all_admins:
        print("\n👑 Resetting admin FCM tokens...")
        success_admins = reset_fcm_token_for_admins(reset_all=True, role_filter=admin_role_filter)
    
    if not reset_all_users and not reset_all_admins:
        print("\n💡 Use specific reset functions instead:")
        print("   - Reset users: reset_fcm_token_for_users()")
        print("   - Reset admins: reset_fcm_token_for_admins()")
        return False
    
    if success_users or success_admins:
        print("\n✅ Reset completed successfully!")
        return True
    else:
        print("\n⚠️  Reset completed with errors")
        return False


def check_fcm_token_status():
    """
    Check FCM token status for both users and admins
    """
    try:
        if firebase_manager.db is None:
            print("❌ Firestore client not initialized")
            return
        
        print("=" * 60)
        print("🔍 CHECKING FCM TOKEN STATUS")
        print("=" * 60)
        
        # Check users
        print("\n👥 CHECKING USERS:")
        print("-" * 60)
        
        users_ref = firebase_manager.db.collection('whitelist_users')
        all_users = users_ref.stream()
        
        users_without_field = []
        users_with_field_empty = []
        users_with_field_filled = []
        
        for doc in all_users:
            user_data = doc.to_dict()
            email = user_data.get('email', 'unknown')
            
            if 'fcmToken' not in user_data:
                users_without_field.append(email)
            elif not user_data.get('fcmToken') or user_data.get('fcmToken').strip() == '':
                users_with_field_empty.append(email)
            else:
                fcm_token = user_data.get('fcmToken', '')
                users_with_field_filled.append((email, fcm_token))
        
        print(f"\n❌ Without fcmToken field ({len(users_without_field)}):")
        for email in users_without_field:
            print(f"   • {email}")
        
        print(f"\n⚠️  With fcmToken field but EMPTY ({len(users_with_field_empty)}):")
        for email in users_with_field_empty:
            print(f"   • {email}")
        
        print(f"\n✅ With fcmToken field and FILLED ({len(users_with_field_filled)}):")
        for email, token in users_with_field_filled:
            print(f"   • {email}: {token[:20]}...{token[-10:]}")
        
        # Check admins
        print("\n\n👑 CHECKING ADMINS:")
        print("-" * 60)
        
        admins_ref = firebase_manager.db.collection('admin_users')
        all_admins = admins_ref.stream()
        
        admins_without_field = []
        admins_with_field_empty = []
        admins_with_field_filled = []
        
        for doc in all_admins:
            admin_data = doc.to_dict()
            email = admin_data.get('email', 'unknown')
            role = admin_data.get('role', 'admin')
            
            if 'fcmToken' not in admin_data:
                admins_without_field.append((email, role))
            elif not admin_data.get('fcmToken') or admin_data.get('fcmToken').strip() == '':
                admins_with_field_empty.append((email, role))
            else:
                fcm_token = admin_data.get('fcmToken', '')
                admins_with_field_filled.append((email, role, fcm_token))
        
        print(f"\n❌ Without fcmToken field ({len(admins_without_field)}):")
        for email, role in admins_without_field:
            print(f"   • {email} ({role})")
        
        print(f"\n⚠️  With fcmToken field but EMPTY ({len(admins_with_field_empty)}):")
        for email, role in admins_with_field_empty:
            print(f"   • {email} ({role})")
        
        print(f"\n✅ With fcmToken field and FILLED ({len(admins_with_field_filled)}):")
        for email, role, token in admins_with_field_filled:
            print(f"   • {email} ({role}): {token[:20]}...{token[-10:]}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"\nUSERS:")
        print(f"   Without field: {len(users_without_field)}")
        print(f"   With empty field: {len(users_with_field_empty)}")
        print(f"   With filled field: {len(users_with_field_filled)}")
        print(f"\nADMINS:")
        print(f"   Without field: {len(admins_without_field)}")
        print(f"   With empty field: {len(admins_with_field_empty)}")
        print(f"   With filled field: {len(admins_with_field_filled)}")
        
        print("\n💡 ACTION REQUIRED:")
        if len(users_without_field) > 0 or len(admins_without_field) > 0:
            print("   ⚠️  Some users/admins need fcmToken field added")
            print("   🔧 Run migration to add fcmToken field")
        
        if len(users_with_field_empty) > 0 or len(admins_with_field_empty) > 0:
            print("   ⚠️  Some users/admins have empty fcmToken")
            print("   🔧 Users/admins need to login to app to save their FCM token")
        
        if len(users_with_field_filled) > 0 or len(admins_with_field_filled) > 0:
            print("   ✅ Some users/admins ready to receive signals")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error checking FCM token status: {e}")
        import traceback
        traceback.print_exc()


def custom_migration():
    """
    Template for custom migration
    Add your custom migration logic here
    """
    try:
        if firebase_manager.db is None:
            print("❌ Firestore client not initialized")
            return False
        
        print("=" * 60)
        print("🔧 CUSTOM MIGRATION")
        print("=" * 60)
        
        # Add your custom migration logic here
        print("\n💡 No custom migration defined yet")
        print("   Edit migrations.py -> custom_migration() to add your logic")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom migration error: {e}")
        import traceback
        traceback.print_exc()
        return False