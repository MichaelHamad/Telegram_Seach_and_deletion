"""
Configuration settings for Telegram message search and deletion tool.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram API credentials
    API_ID = os.getenv('API_ID')
    API_HASH = os.getenv('API_HASH')
    PHONE_NUMBER = os.getenv('PHONE_NUMBER')
    SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')
    
    # File paths
    EXPORT_DIR = 'exports'
    OUTPUT_DIR = 'output'
    LOGS_DIR = 'logs'
    
    # Deletion settings
    BATCH_SIZE = 100  # Number of messages to delete in each batch
    DELAY_BETWEEN_BATCHES = 2  # Seconds to wait between batches
    DRY_RUN = True  # Set to False to actually delete messages
    
    # Search settings
    DEFAULT_KEYWORDS = [
        # Add your keywords here as regex patterns
        # Example: r'\bpassword\b', r'\btoken\b', r'\bsecret\b'
    ]
    
    # Chat filtering (optional)
    INCLUDE_CHAT_TYPES = ['private', 'group', 'supergroup', 'channel']
    EXCLUDE_CHATS = []  # List of chat IDs or usernames to exclude
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required = ['API_ID', 'API_HASH', 'PHONE_NUMBER']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
