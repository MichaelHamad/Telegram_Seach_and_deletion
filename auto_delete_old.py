#!/usr/bin/env python3
"""
Auto Delete Old Telegram Messages (No User Input Required)
Deletes all messages except those sent in the last 24 hours.
"""
import asyncio
from datetime import datetime, timedelta
from json_analyzer import TelegramJSONAnalyzer
from telegram_deleter import TelegramDeleter
from config import Config

# ========================================
# CONFIGURATION - EDIT THESE VALUES
# ========================================

# Path to your Telegram export file
# Leave empty ("") to use API-only mode (searches Telegram directly)
# API-only mode: Slower but works without export file
# Export file mode: Faster and more reliable
EXPORT_FILE = "/path/to/your/export.json"

# Hours to keep (messages newer than this will be kept)
HOURS_TO_KEEP = 24

# Keywords to search for (add or remove as needed)
# Empty list = delete ALL old messages
KEYWORDS = [
]

# Search options
CASE_SENSITIVE = False  # Set to True for case sensitive search
WHOLE_WORDS = True      # Set to False to allow partial matches

async def api_only_delete_messages(hours_to_keep: int = 24, keywords: list = None, case_sensitive: bool = False, whole_words: bool = True):
    """Delete messages using API-only mode (no export file needed)."""
    
    print("🗑️  API-Only Telegram Message Deletion")
    print("=" * 50)
    print("🔌 Using Telegram API directly (no export file)")
    print(f"⏰ Keeping messages from last {hours_to_keep} hours")
    if keywords and len(keywords) > 0:
        print(f"🔎 Keywords: {', '.join(keywords)}")
    else:
        print("🔍 Deleting ALL old messages (no keyword filter)")
    print(f"⚙️  Case sensitive: {case_sensitive}")
    print(f"⚙️  Whole words only: {whole_words}")
    print()
    
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated")
        
        # Initialize deleter
        deleter = TelegramDeleter(
            Config.API_ID,
            Config.API_HASH,
            Config.PHONE_NUMBER,
            Config.SESSION_NAME
        )
        
        # Connect to Telegram
        print("🔌 Connecting to Telegram...")
        if not await deleter.connect():
            print("❌ Failed to connect to Telegram")
            return
        
        try:
            # Get all dialogs (chats)
            print("📂 Loading your chats...")
            dialogs = await deleter.client.get_dialogs()
            print(f"📊 Found {len(dialogs)} chats")
            
            # Calculate cutoff time
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=hours_to_keep)
            print(f"⏰ Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            messages_to_delete = []
            total_processed = 0
            
            # Search through each chat
            for dialog in dialogs:
                chat_name = dialog.name or f"Chat_{dialog.id}"
                print(f"🔍 Searching {chat_name}...")
                
                try:
                    # Get messages from this chat
                    messages = await deleter.client.get_messages(dialog, limit=None)
                    
                    for message in messages:
                        total_processed += 1
                        
                        # Check if message is from us
                        if not message.out:
                            continue
                        
                        # Check if message is old enough
                        if message.date < cutoff_time:
                            # Check keywords if specified
                            if keywords and len(keywords) > 0:
                                message_text = str(message.text or "").lower()
                                keyword_found = False
                                
                                for keyword in keywords:
                                    search_keyword = keyword.lower() if not case_sensitive else keyword
                                    
                                    if whole_words:
                                        # Whole word matching
                                        import re
                                        pattern = rf'\b{re.escape(search_keyword)}\b'
                                        if re.search(pattern, message_text, re.IGNORECASE if not case_sensitive else 0):
                                            keyword_found = True
                                            break
                                    else:
                                        # Partial matching
                                        if search_keyword in message_text:
                                            keyword_found = True
                                            break
                                
                                if not keyword_found:
                                    continue
                            
                            # Add to deletion list
                            messages_to_delete.append({
                                'chat_entity': dialog,
                                'message_id': message.id,
                                'chat_name': chat_name,
                                'date': message.date,
                                'text': str(message.text or "")[:50] + "..." if len(str(message.text or "")) > 50 else str(message.text or "")
                            })
                
                except Exception as e:
                    print(f"⚠️  Error processing {chat_name}: {e}")
                    continue
            
            print(f"\n📊 Search complete!")
            print(f"📊 Total messages processed: {total_processed}")
            print(f"🗑️  Messages to delete: {len(messages_to_delete)}")
            
            if not messages_to_delete:
                print("✅ No messages found to delete.")
                return
            
            # Show summary by chat
            chat_counts = {}
            for msg in messages_to_delete:
                chat_name = msg['chat_name']
                chat_counts[chat_name] = chat_counts.get(chat_name, 0) + 1
            
            print(f"\n📋 Messages to delete by chat:")
            for chat, count in sorted(chat_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {chat}: {count} messages")
            if len(chat_counts) > 10:
                print(f"  ... and {len(chat_counts) - 10} more chats")
            
            # Delete messages
            print(f"\n🗑️  Starting deletion of {len(messages_to_delete)} messages...")
            
            deleted_count = 0
            failed_count = 0
            
            for msg in messages_to_delete:
                try:
                    success, error_msg = await deleter.delete_message(
                        msg['chat_entity'], 
                        msg['message_id'], 
                        revoke=True, 
                        dry_run=False
                    )
                    
                    if success:
                        deleted_count += 1
                        if deleted_count % 100 == 0:
                            print(f"✅ Deleted {deleted_count}/{len(messages_to_delete)} messages...")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to delete message in {msg['chat_name']}: {error_msg}")
                
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error deleting message in {msg['chat_name']}: {e}")
            
            # Print final results
            print(f"\n" + "="*50)
            print(f"✅ DELETION COMPLETE!")
            print(f"="*50)
            print(f"Successfully deleted: {deleted_count}")
            print(f"Failed: {failed_count}")
            print(f"Total processed: {len(messages_to_delete)}")
            
        finally:
            await deleter.disconnect()
            print("\n🔌 Disconnected from Telegram")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return

async def auto_delete_old_messages(export_file: str, hours_to_keep: int = 24, keywords: list = None, case_sensitive: bool = False, whole_words: bool = True):
    """Delete messages older than specified hours, optionally filtered by keywords."""
    
    print("🗑️  Auto Delete Old Telegram Messages")
    print("=" * 50)
    print(f"📂 Export file: {export_file}")
    print(f"⏰ Keeping messages from last {hours_to_keep} hours")
    if keywords and len(keywords) > 0:
        print(f"🔍 Only deleting messages containing: {', '.join(keywords)}")
    else:
        print("🔍 Deleting ALL old messages (no keyword filter)")
    print()
    
    try:
        # Validate configuration
        Config.validate()
        print("✅ Configuration validated")
        
        # Initialize analyzer
        analyzer = TelegramJSONAnalyzer(export_file)
        
        # Load and process data
        print("📂 Loading Telegram export...")
        analyzer.load_export()
        
        print("📊 Extracting outgoing messages...")
        analyzer.extract_outgoing_messages()
        
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours_to_keep)
        print(f"⏰ Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Filter messages older than cutoff
        all_messages = analyzer.messages_df
        old_messages = all_messages[all_messages['date'] < cutoff_time]
        recent_messages = all_messages[all_messages['date'] >= cutoff_time]
        
        # Apply keyword filter if specified
        if keywords and len(keywords) > 0:
            print(f"🔍 Filtering old messages by keywords: {', '.join(keywords)}")
            # Use the analyzer's keyword search function
            keyword_matches = analyzer.find_messages_by_keywords(
                keywords, 
                case_sensitive=case_sensitive,
                whole_words=whole_words
            )
            # Only keep old messages that match keywords
            old_messages = old_messages[old_messages['message_id'].isin(keyword_matches['message_id'])]
            print(f"📊 After keyword filtering: {len(old_messages)} messages to delete")
        else:
            print("🔍 No keyword filter - will delete ALL old messages")
        
        print(f"📊 Total messages: {len(all_messages)}")
        print(f"🗑️  Messages to delete (older than {hours_to_keep}h): {len(old_messages)}")
        print(f"✅ Messages to keep (last {hours_to_keep}h): {len(recent_messages)}")
        
        if old_messages.empty:
            print("✅ No old messages found to delete.")
            return
        
        # Show summary by chat
        print(f"\n📋 Messages to delete by chat:")
        chat_counts = old_messages['chat_name'].value_counts()
        for chat, count in chat_counts.head(10).items():
            print(f"  - {chat}: {count} messages")
        if len(chat_counts) > 10:
            print(f"  ... and {len(chat_counts) - 10} more chats")
        
        # Save preview
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f"output/old_messages_to_delete_{timestamp}.csv"
        preview_columns = ['chat_name', 'chat_type', 'message_id', 'date', 'text']
        preview_df = old_messages[preview_columns].copy()
        preview_df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"📄 Preview saved to: {csv_file}")
        
        print(f"\n🚀 Starting deletion of {len(old_messages)} old messages...")
        
        # Initialize deleter
        deleter = TelegramDeleter(
            Config.API_ID,
            Config.API_HASH,
            Config.PHONE_NUMBER,
            Config.SESSION_NAME
        )
        
        # Connect to Telegram
        print("🔌 Connecting to Telegram...")
        if not await deleter.connect():
            print("❌ Failed to connect to Telegram")
            return
        
        try:
            # Delete messages
            print(f"🗑️  Deleting {len(old_messages)} old messages...")
            stats = await deleter.delete_messages_batch(
                old_messages,
                dry_run=False,
                batch_size=Config.BATCH_SIZE,
                delay_between_batches=Config.DELAY_BETWEEN_BATCHES
            )
            
            # Print results
            deleter.print_statistics()
            
            # Save error report if there were errors
            if stats.get('errors'):
                deleter.save_error_report()
                print(f"\n📄 Error report saved - check for any failed deletions")
            
        finally:
            await deleter.disconnect()
            print("\n🔌 Disconnected from Telegram")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return

def main():
    # ========================================
    # DELETION CODE - NO NEED TO EDIT BELOW
    # ========================================
    
    # Check if using API-only mode
    if not EXPORT_FILE or EXPORT_FILE.strip() == "":
        print("🔌 API-Only Mode: No export file specified")
        asyncio.run(api_only_delete_messages(HOURS_TO_KEEP, KEYWORDS, CASE_SENSITIVE, WHOLE_WORDS))
    else:
        print("📂 Export File Mode: Using export file")
        print(f"📂 Export file: {EXPORT_FILE}")
        print(f"⏰ Keeping messages from last {HOURS_TO_KEEP} hours")
        if KEYWORDS and len(KEYWORDS) > 0:
            print(f"🔎 Keywords: {', '.join(KEYWORDS)}")
        else:
            print("🔍 Deleting ALL old messages (no keyword filter)")
        print(f"⚙️  Case sensitive: {CASE_SENSITIVE}")
        print(f"⚙️  Whole words only: {WHOLE_WORDS}")
        print()
        
        asyncio.run(auto_delete_old_messages(EXPORT_FILE, HOURS_TO_KEEP, KEYWORDS, CASE_SENSITIVE, WHOLE_WORDS))

if __name__ == '__main__':
    main()
