# Usage Guide

## 📋 Script Overview

| Script | Purpose | Speed | API Required |
|--------|---------|-------|--------------|
| `auto_delete_old.py` | Delete old messages automatically | Fast (5-10 min) | Yes |
| `complete_analyzer.py` | Analyze and create manual guides | Very Fast (1-2 min) | No |

## 📁 Getting Your Telegram JSON Export

### Why You Need the Export File
- **10x faster** than API-only mode
- **More reliable** - works with historical data
- **Required** for `complete_analyzer.py`
- **Recommended** for `auto_delete_old.py`

### Step-by-Step Export Instructions

#### 1. Download Telegram Desktop
- Go to https://desktop.telegram.org/
- Download and install for your operating system
- Log in with your phone number

#### 2. Access Export Settings
- Open Telegram Desktop
- Click the **hamburger menu** (☰) in top-left corner
- Go to **Settings** (gear icon)
- Click **Advanced** in the left sidebar
- Click **Export Telegram Data**

#### 3. Configure Export Options
- **Format**: Select **JSON** (not HTML)
- **Media**: Uncheck "Include media" (faster export, smaller file)
- **Date Range**: Leave as "All time" or select specific range
- **Chats**: Leave as "All chats" or select specific chats

#### 4. Start the Export
- Click **Export** button
- Wait for completion (10-30 minutes for large accounts)
- The export will be saved to your Downloads folder

#### 5. Find Your Export File
Look for a folder named `DataExport_YYYY-MM-DD` in your Downloads folder:
```
/Users/username/Downloads/Telegram Desktop/DataExport_2025-09-27/
├── result.json          ← This is what you need
├── chats/
├── media/
└── other files...
```

#### 6. Update Your Script Configuration
Use the full path to `result.json` in your scripts:
```python
EXPORT_FILE = "/Users/username/Downloads/Telegram Desktop/DataExport_2025-09-27/result.json"
```

### Export File Tips
- **File size**: Can be 100MB+ for active users
- **Export time**: 10-30 minutes depending on account size
- **Media**: Excluding media makes export much faster
- **Format**: Must be JSON, not HTML
- **Location**: Usually in Downloads/Telegram Desktop/DataExport_YYYY-MM-DD/

## 🔧 auto_delete_old.py - Automated Deletion

### Configuration Options

```python
# ========================================
# CONFIGURATION - EDIT THESE VALUES
# ========================================

# Export file path (empty for API-only mode)
EXPORT_FILE = "/path/to/your/export.json"

# Hours to keep (messages newer than this will be kept)
HOURS_TO_KEEP = 24

# Keywords to search for (empty list = delete all old messages)
KEYWORDS = ["password", "card", "credit"]

# Search options
CASE_SENSITIVE = False  # Set to True for case sensitive search
WHOLE_WORDS = True      # Set to False to allow partial matches
```

### Usage Examples

#### Delete All Messages Older Than 24 Hours
```python
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 24
KEYWORDS = []  # Empty = delete all old messages
```

#### Delete Messages with Sensitive Keywords
```python
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 24
KEYWORDS = ["password", "credit card", "ssn", "social security"]
```

#### Delete Messages Older Than 1 Week
```python
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 168  # 7 days * 24 hours
KEYWORDS = []
```

#### API-Only Mode (No Export File)
```python
EXPORT_FILE = ""  # Empty = API-only mode
HOURS_TO_KEEP = 24
KEYWORDS = []
```

### Running the Script
```bash
python auto_delete_old.py
```

**What happens:**
1. Loads your export file (if specified)
2. Connects to Telegram API
3. Asks for verification code
4. Finds messages to delete
5. Deletes them in batches
6. Shows progress and results

## 🔍 complete_analyzer.py - Analysis Only

### Configuration Options

```python
# ========================================
# CONFIGURATION - EDIT THESE VALUES
# ========================================

# Path to your Telegram export file
EXPORT_FILE = "/path/to/your/export.json"

# Keywords to search for
KEYWORDS = ["password", "card", "credit"]

# Search options
CASE_SENSITIVE = False
WHOLE_WORDS = True
```

### Usage Examples

#### Find All Messages with Sensitive Keywords
```python
EXPORT_FILE = "/path/to/export.json"
KEYWORDS = ["password", "credit card", "ssn"]
```

#### Find Messages with Financial Terms
```python
EXPORT_FILE = "/path/to/export.json"
KEYWORDS = ["bank", "account", "routing", "wire transfer"]
```

#### Case-Sensitive Search
```python
EXPORT_FILE = "/path/to/export.json"
KEYWORDS = ["Password", "PASSWORD", "password"]
CASE_SENSITIVE = True
```

### Running the Script
```bash
python complete_analyzer.py
```

**What happens:**
1. Loads your export file
2. Searches for matching messages
3. Creates CSV file with results
4. Generates markdown deletion guide
5. Shows summary statistics

**Output files:**
- `output/keyword_matches_YYYYMMDD_HHMMSS.csv` - Detailed results
- `output/deletion_guide_YYYYMMDD_HHMMSS.md` - Manual deletion guide

## ⚙️ Advanced Configuration

### Search Options

#### Case Sensitivity
```python
CASE_SENSITIVE = True   # "Password" ≠ "password"
CASE_SENSITIVE = False  # "Password" = "password"
```

#### Whole Words vs Partial Matches
```python
WHOLE_WORDS = True   # "card" matches "credit card" but not "discard"
WHOLE_WORDS = False  # "card" matches "credit card" and "discard"
```

### Time Filtering

#### Keep Recent Messages
```python
HOURS_TO_KEEP = 24    # Keep last 24 hours
HOURS_TO_KEEP = 168   # Keep last week (7 days)
HOURS_TO_KEEP = 720   # Keep last month (30 days)
```

#### Delete Everything
```python
HOURS_TO_KEEP = 0     # Delete everything (no time filter)
```

## 🚨 Safety Tips

1. **Always test first**: Start with `HOURS_TO_KEEP = 1` to test
2. **Backup important messages**: Export before mass deletion
3. **Use dry run**: Check what will be deleted before confirming
4. **Close Telegram Desktop**: Prevents database conflicts
5. **Check your export file**: Ensure it's recent and complete

## 📊 Understanding Results

### auto_delete_old.py Output
```
📊 Total messages: 16583
🗑️  Messages to delete (older than 24h): 16582
✅ Messages to keep (last 24h): 1

📋 Messages to delete by chat:
  - Shoorik: 2847 messages
  - Locked In FNF: 2329 messages
  - Monaco Cabal: 1206 messages
  ...
```

### complete_analyzer.py Output
```
📊 Found 45 messages matching your keywords
📄 CSV file: output/keyword_matches_20250927_224317.csv
📋 Deletion guide: output/deletion_guide_20250927_224317.md
```

## 🆘 Troubleshooting

### JSON Export Issues

**"Export file not found"**
- Check the file path is correct
- Look for `DataExport_YYYY-MM-DD/result.json`
- Make sure export completed successfully

**"Invalid JSON format"**
- Ensure you selected JSON format (not HTML)
- Try re-exporting your data
- Check file isn't corrupted

**"Export taking too long"**
- Uncheck "Include media" for faster export
- Select specific date range instead of "All time"
- Close other applications to free up resources

**"Can't find export button"**
- Make sure you're using Telegram Desktop (not web)
- Go to Settings → Advanced → Export Telegram Data
- Update Telegram Desktop to latest version

### API Connection Issues

**"Database is locked"**
- Close Telegram Desktop completely
- Wait 10 seconds
- Run script again

**"Cannot send requests while disconnected"**
- Check internet connection
- Use export file mode instead
- Restart script

**"Message not found"**
- Use export file mode (more reliable)
- Some chats may be inaccessible
- Messages already deleted

**"Failed to connect to Telegram"**
- Check API credentials in .env file
- Verify phone number format (+1234567890)
- Run in terminal, not IDE
- Make sure you're not rate limited
