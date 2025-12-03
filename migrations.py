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
            print("   📝 Run migration to add fcmToken field")
        
        if len(users_with_field_empty) > 0 or len(admins_with_field_empty) > 0:
            print("   ⚠️  Some users/admins have empty fcmToken")
            print("   📝 Users/admins need to login to app to save their FCM token")
        
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