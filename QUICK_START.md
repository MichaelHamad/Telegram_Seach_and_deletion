# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup API Credentials
```bash
# Copy the template
cp env_template .env

# Edit with your credentials
nano .env
```

Add your Telegram API credentials:
```bash
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890
SESSION_NAME=telegram_cleanup
```

### Step 3: Export Your Data (Recommended)

**Detailed Export Instructions:**

1. **Open Telegram Desktop**
   - Download from https://desktop.telegram.org/
   - Log in with your phone number

2. **Navigate to Export**
   - Click hamburger menu (☰) → Settings → Advanced
   - Click "Export Telegram Data"

3. **Configure Export**
   - **Format**: JSON (not HTML)
   - **Media**: Uncheck (faster, smaller file)
   - **Date Range**: All time
   - **Chats**: All chats

4. **Export and Download**
   - Click "Export" button
   - Wait 10-30 minutes for completion
   - Find folder: `DataExport_YYYY-MM-DD/result.json`

**Example path:**
```
/Users/username/Downloads/Telegram Desktop/DataExport_2025-09-27/result.json
```

### Step 4: Configure and Run
Edit `auto_delete_old.py`:
```python
# Set your export file path
EXPORT_FILE = "/path/to/your/export.json"

# Set how many hours to keep (24 = delete everything older than 24 hours)
HOURS_TO_KEEP = 24

# Set keywords (empty list = delete all old messages)
KEYWORDS = []  # or ["password", "card", "credit"]
```

### Step 5: Run the Script
```bash
python auto_delete_old.py
```

Enter the verification code when prompted.

## 🎯 Common Use Cases

### Delete All Old Messages
```python
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 24
KEYWORDS = []  # Empty = delete all old
```

### Delete Sensitive Messages
```python
EXPORT_FILE = "/path/to/export.json"
HOURS_TO_KEEP = 24
KEYWORDS = ["password", "credit card", "ssn"]
```

### Analyze Without Deleting
```bash
python complete_analyzer.py
```

## ⚠️ Important Notes

- **Close Telegram Desktop** before running
- **Backup important messages** before deletion
- **Test with a small time window** first (e.g., 1 hour)
- **Export file mode is much faster** than API-only

## 🆘 Need Help?

1. Check the main README.md for detailed documentation
2. Ensure your API credentials are correct
3. Try export file mode if API-only is slow
4. Close Telegram Desktop if you get database errors
