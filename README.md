# Telegram Message Cleanup Tool

A powerful Python tool for finding and deleting Telegram messages based on keywords or time filters. Supports both automated deletion via Telegram API and manual deletion guides.

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env_template .env

# Edit .env with your Telegram API credentials
nano .env
```

### 2. Get Telegram API Credentials
1. Go to https://my.telegram.org/apps
2. Create a new application
3. Copy your `API_ID` and `API_HASH`
4. Add your phone number (with country code, e.g., +1234567890)

### 3. Export Your Telegram Data (Optional but Recommended)

**Step-by-Step Export Instructions:**

1. **Open Telegram Desktop**
   - Download from https://desktop.telegram.org/ if you don't have it
   - Log in with your phone number

2. **Access Export Settings**
   - Click the hamburger menu (☰) in the top left
   - Go to **Settings** (gear icon)
   - Click **Advanced** in the left sidebar
   - Click **Export Telegram Data**

3. **Configure Export Options**
   - **Format**: Select **JSON** (not HTML)
   - **Media**: Uncheck "Include media" (faster export, smaller file)
   - **Date Range**: Leave as "All time" or select specific range
   - **Chats**: Leave as "All chats" or select specific chats

4. **Start Export**
   - Click **Export** button
   - Wait for export to complete (can take 10-30 minutes for large accounts)
   - Note the download location (usually Downloads folder)

5. **Find Your Export File**
   - Look for a folder named `DataExport_YYYY-MM-DD`
   - Inside, find `result.json` file
   - Copy the full path to this file

**Example Export Path:**
```
/Users/username/Downloads/Telegram Desktop/DataExport_2025-09-27/result.json
```

**Note**: The export file can be large (100MB+ for active users). JSON format is required for the scripts to work.

## 📋 Available Scripts

### `auto_delete_old.py` - Main Deletion Script
**Purpose**: Delete old messages automatically using Telegram API

**Features**:
- Delete all messages older than X hours
- Optional keyword filtering
- Export file mode (fast) or API-only mode
- Batch processing with rate limiting
- Progress tracking and error handling

**Usage**:
```bash
python auto_delete_old.py
```

**Configuration** (edit at top of file):
```python
# Path to export file (empty for API-only mode)
EXPORT_FILE = "/path/to/your/export.json"

# Hours to keep (messages newer than this will be kept)
HOURS_TO_KEEP = 24

# Keywords to filter by (empty list = delete all old messages)
KEYWORDS = ["password", "card", "credit"]

# Search options
CASE_SENSITIVE = False
WHOLE_WORDS = True
```

### `complete_analyzer.py` - Analysis & Manual Guide
**Purpose**: Analyze messages and create manual deletion guides

**Features**:
- Find messages by keywords
- Generate CSV with matching messages
- Create markdown deletion guide
- No API required (analysis only)

**Usage**:
```bash
python complete_analyzer.py
```

**Configuration** (edit at top of file):
```python
# Path to export file
EXPORT_FILE = "/path/to/your/export.json"

# Keywords to search for
KEYWORDS = ["password", "card", "credit"]

# Search options
CASE_SENSITIVE = False
WHOLE_WORDS = True
```

## 🔧 Configuration

### Environment Variables (.env file)
```bash
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890
SESSION_NAME=telegram_cleanup
```

### Export File vs API-Only Mode

**Export File Mode (Recommended)**:
- ✅ Faster (5-10 minutes)
- ✅ More reliable
- ✅ Works with historical data
- ❌ Requires export file

**API-Only Mode**:
- ✅ No export file needed
- ✅ Always current data
- ❌ Slower (1-2 hours)
- ❌ Rate limited by Telegram

## 📊 Usage Examples

### Example 1: Delete All Old Messages (24+ hours)
```python
# In auto_delete_old.py
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 24
KEYWORDS = []  # Empty = delete all old messages
```

### Example 2: Delete Messages with Sensitive Keywords
```python
# In auto_delete_old.py
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 24
KEYWORDS = ["password", "credit card", "ssn", "social security"]
```

### Example 3: Analyze Without Deleting
```python
# In complete_analyzer.py
EXPORT_FILE = "/path/to/export.json"
KEYWORDS = ["password", "card", "credit"]
```

## 🛠️ Troubleshooting

### Common Issues

**1. "Database is locked"**
- Close Telegram Desktop completely
- Wait 10 seconds
- Run script again

**2. "Cannot send requests while disconnected"**
- Check your internet connection
- Restart the script
- Use export file mode instead

**3. "Message not found" errors**
- Use export file mode (more reliable)
- Some chats may be inaccessible
- Messages may have been already deleted

**4. "Failed to connect to Telegram"**
- Check your API credentials in .env
- Ensure phone number includes country code
- Try running in terminal instead of IDE

### Rate Limiting
- Telegram imposes delays (10-12 seconds) between batches
- This is normal and cannot be avoided
- Export file mode is much faster

## 📁 Project Structure

```
Telegram_Seach_and_deletion/
├── auto_delete_old.py          # Main deletion script
├── complete_analyzer.py        # Analysis and manual guide
├── config.py                   # Configuration management
├── json_analyzer.py           # JSON export processing
├── telegram_deleter.py        # Telegram API deletion logic
├── requirements.txt           # Python dependencies
├── env_template              # Environment variables template
├── README.md                 # This documentation
└── exports/                  # Your export files go here
```

## 🔒 Security Notes

- Never commit your `.env` file to version control
- The `.env` file contains sensitive API credentials
- Session files are automatically created and should be kept private
- Always review messages before deletion

## 📈 Performance Tips

1. **Use Export File Mode**: 10x faster than API-only
2. **Empty Keywords**: Faster than keyword filtering
3. **Smaller Time Windows**: Fewer messages to process
4. **Close Telegram Desktop**: Prevents database locks

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your API credentials
3. Try export file mode instead of API-only
4. Check your internet connection
5. Ensure Telegram Desktop is closed

## 📝 License

This tool is for personal use only. Use responsibly and in accordance with Telegram's Terms of Service.