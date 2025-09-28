#!/usr/bin/env python3
"""
Complete Telegram Message Analyzer with Auto Guide Generation
Reads the export file directly, lets you specify keywords, and creates deletion guide.
"""
from json_analyzer import TelegramJSONAnalyzer
import os
from datetime import datetime

def create_simple_guide(matches_df, csv_file):
    """Create a simple deletion guide."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    guide_file = f"output/deletion_guide_{timestamp}.md"
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Group by chat
    chat_groups = matches_df.groupby('chat_name')
    
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write("# Telegram Message Deletion Guide\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total messages to delete:** {len(matches_df)}\n")
        f.write(f"**CSV file:** `{csv_file}`\n\n")
        
        f.write("## Instructions\n\n")
        f.write("1. Open Telegram Desktop or Mobile\n")
        f.write("2. Go to each chat listed below\n")
        f.write("3. Find and delete the messages with matching text\n")
        f.write("4. Check off each chat as you complete it\n\n")
        
        f.write("## Chats to Process\n\n")
        
        for chat_name, group in chat_groups:
            f.write(f"### {chat_name} ({len(group)} messages)\n")
            f.write("- [ ] **Status:** Not started\n\n")
            
            # Show first few messages as examples
            for i, (_, row) in enumerate(group.head(3).iterrows()):
                message_text = str(row.get('text', ''))[:100]
                if len(str(row.get('text', ''))) > 100:
                    message_text += "..."
                f.write(f"  - Example: \"{message_text}\"\n")
            
            if len(group) > 3:
                f.write(f"  - ... and {len(group) - 3} more messages\n")
            f.write("\n")
    
    return guide_file

def main():
    # ========================================
    # CONFIGURATION - EDIT THESE VALUES
    # ========================================
    
    # Path to your Telegram export file
    EXPORT_FILE = "/Users/michaelhamad/Downloads/Telegram Desktop/DataExport_2025-09-27_v2/result.json"
    
    # Keywords to search for (add or remove as needed)
    KEYWORDS = [
        "password",
        "card", 
        "credit",
        "address",
        "phone"
    ]
    
    # Search options
    CASE_SENSITIVE = False  # Set to True for case sensitive search
    WHOLE_WORDS = True      # Set to False to allow partial matches
    
    # ========================================
    # ANALYSIS CODE - NO NEED TO EDIT BELOW
    # ========================================
    
    print("🔍 Complete Telegram Message Analyzer")
    print("=" * 50)
    print(f"📂 Export file: {EXPORT_FILE}")
    print(f"🔎 Keywords: {', '.join(KEYWORDS)}")
    print(f"⚙️  Case sensitive: {CASE_SENSITIVE}")
    print(f"⚙️  Whole words only: {WHOLE_WORDS}")
    print()
    
    try:
        # Initialize analyzer
        analyzer = TelegramJSONAnalyzer(EXPORT_FILE)
        
        # Load and process data
        print("📂 Loading Telegram export...")
        analyzer.load_export()
        
        print("📊 Extracting outgoing messages...")
        analyzer.extract_outgoing_messages()
        
        # Find matches
        print(f"🔎 Searching for keywords...")
        matches = analyzer.find_messages_by_keywords(
            KEYWORDS, 
            case_sensitive=CASE_SENSITIVE,
            whole_words=WHOLE_WORDS
        )
        
        # Print summary
        analyzer.print_summary(matches)
        
        if not matches.empty:
            # Save preview CSV
            csv_file = analyzer.save_preview_csv(matches)
            
            # Create simple deletion guide
            print("\n📋 Creating deletion guide...")
            guide_file = create_simple_guide(matches, csv_file)
            
            print("\n" + "=" * 50)
            print("✅ ANALYSIS COMPLETE!")
            print("=" * 50)
            print(f"📄 CSV file: {csv_file}")
            print(f"📋 Deletion guide: {guide_file}")
            print()
            print("📱 Next steps:")
            print("1. Open the deletion guide (markdown file)")
            print("2. Follow the chat-by-chat instructions")
            print("3. Use the checklist to track your progress")
            print("4. Delete messages in Telegram manually")
            
        else:
            print("✅ No messages found matching your keywords.")
            print("💡 Try different keywords or check your export file.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == '__main__':
    main()
