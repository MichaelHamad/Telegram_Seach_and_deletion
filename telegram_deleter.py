"""
Telegram Message Deleter using Telethon
Provides safe bulk deletion of Telegram messages with dry-run mode and batch processing.
"""
import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChatAdminRequiredError, MessageDeleteForbiddenError
from telethon.tl.types import Message
import time
import logging
from pathlib import Path
from tqdm import tqdm
import colorama
from colorama import Fore, Style

# Initialize colorama for colored output
colorama.init()

class TelegramDeleter:
    def __init__(self, api_id: str, api_hash: str, phone_number: str, 
                 session_name: str = 'telegram_session'):
        """
        Initialize the Telegram deleter.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone_number: Phone number with country code
            session_name: Name for the session file
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_name = session_name
        self.client = None
        
        # Setup logging
        self.setup_logging()
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successfully_deleted': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'deletion_log_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """
        Connect to Telegram and authenticate.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start(phone=self.phone_number)
            
            # Verify connection
            me = await self.client.get_me()
            self.logger.info(f"Connected as: {me.first_name} {me.last_name} (@{me.username})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
    
    async def find_chat_by_name_or_id(self, chat_identifier: str) -> Optional[Any]:
        """
        Find a chat by name or ID.
        
        Args:
            chat_identifier: Chat name, username, or ID
        
        Returns:
            Chat entity or None if not found
        """
        try:
            # Try to get chat directly by ID if it's numeric
            if chat_identifier.isdigit() or (chat_identifier.startswith('-') and chat_identifier[1:].isdigit()):
                chat_id = int(chat_identifier)
                return await self.client.get_entity(chat_id)
            
            # Try to find by username
            if chat_identifier.startswith('@'):
                return await self.client.get_entity(chat_identifier)
            
            # Search for chats by name
            dialogs = await self.client.get_dialogs()
            for dialog in dialogs:
                if dialog.name and chat_identifier.lower() in dialog.name.lower():
                    return dialog.entity
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding chat '{chat_identifier}': {e}")
            return None
    
    async def get_message_from_chat(self, chat_entity: Any, message_id: int) -> Optional[Message]:
        """
        Get a specific message from a chat.
        
        Args:
            chat_entity: Chat entity
            message_id: Message ID
        
        Returns:
            Message object or None if not found
        """
        try:
            message = await self.client.get_messages(chat_entity, ids=message_id)
            return message if message else None
        except Exception as e:
            self.logger.error(f"Error getting message {message_id} from chat {chat_entity.id}: {e}")
            return None
    
    async def delete_message(self, chat_entity: Any, message_id: int, 
                           revoke: bool = True, dry_run: bool = True) -> Tuple[bool, str]:
        """
        Delete a single message.
        
        Args:
            chat_entity: Chat entity
            message_id: Message ID
            revoke: Whether to delete for everyone (True) or just for self (False)
            dry_run: If True, only simulate deletion
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if dry_run:
                return True, "DRY RUN: Would delete message"
            
            # Get the message first to verify it exists and is deletable
            message = await self.get_message_from_chat(chat_entity, message_id)
            if not message:
                return False, "Message not found"
            
            # Check if message is from us
            if not message.out:
                return False, "Message is not from you"
            
            # Delete the message
            result = await self.client.delete_messages(chat_entity, [message_id], revoke=revoke)
            
            if result:
                return True, "Message deleted successfully"
            else:
                return False, "Deletion failed"
                
        except FloodWaitError as e:
            wait_time = e.seconds
            self.logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return False, f"Rate limited, waited {wait_time}s"
            
        except ChatAdminRequiredError:
            return False, "Admin rights required"
            
        except MessageDeleteForbiddenError:
            return False, "Message deletion forbidden"
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    async def delete_messages_batch(self, messages_df: pd.DataFrame, 
                                  dry_run: bool = True, 
                                  batch_size: int = 100,
                                  delay_between_batches: float = 2.0) -> Dict[str, Any]:
        """
        Delete messages in batches with progress tracking.
        
        Args:
            messages_df: DataFrame with messages to delete
            dry_run: If True, only simulate deletion
            batch_size: Number of messages per batch
            delay_between_batches: Delay between batches in seconds
        
        Returns:
            Dictionary with deletion statistics
        """
        if messages_df.empty:
            self.logger.warning("No messages to delete")
            return self.stats
        
        self.logger.info(f"Starting {'dry run' if dry_run else 'deletion'} of {len(messages_df)} messages")
        self.logger.info(f"Batch size: {batch_size}, Delay: {delay_between_batches}s")
        
        # Group messages by chat for efficiency
        chat_groups = messages_df.groupby(['chat_id', 'chat_name'])
        
        total_chats = len(chat_groups)
        processed_chats = 0
        
        for (chat_id, chat_name), chat_messages in chat_groups:
            processed_chats += 1
            self.logger.info(f"Processing chat {processed_chats}/{total_chats}: {chat_name} ({len(chat_messages)} messages)")
            
            # Find chat entity
            chat_entity = await self.find_chat_by_name_or_id(str(chat_id))
            if not chat_entity:
                self.logger.error(f"Could not find chat: {chat_name} (ID: {chat_id})")
                self.stats['failed'] += len(chat_messages)
                continue
            
            # Process messages in batches
            message_ids = chat_messages['message_id'].tolist()
            
            for i in range(0, len(message_ids), batch_size):
                batch = message_ids[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(message_ids) + batch_size - 1) // batch_size
                
                self.logger.info(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} messages)")
                
                # Process each message in the batch
                for msg_id in tqdm(batch, desc=f"Batch {batch_num}"):
                    success, message = await self.delete_message(
                        chat_entity, msg_id, revoke=True, dry_run=dry_run
                    )
                    
                    self.stats['total_processed'] += 1
                    
                    if success:
                        if dry_run:
                            self.stats['skipped'] += 1
                        else:
                            self.stats['successfully_deleted'] += 1
                    else:
                        self.stats['failed'] += 1
                        self.stats['errors'].append({
                            'chat_name': chat_name,
                            'message_id': msg_id,
                            'error': message
                        })
                
                # Delay between batches (except for the last batch)
                if i + batch_size < len(message_ids) and delay_between_batches > 0:
                    self.logger.info(f"  Waiting {delay_between_batches}s before next batch...")
                    await asyncio.sleep(delay_between_batches)
        
        return self.stats
    
    def print_statistics(self):
        """Print deletion statistics."""
        print("\n" + "="*50)
        print(f"{Fore.CYAN}DELETION STATISTICS{Style.RESET_ALL}")
        print("="*50)
        print(f"Total processed: {self.stats['total_processed']}")
        print(f"Successfully deleted: {Fore.GREEN}{self.stats['successfully_deleted']}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{self.stats['failed']}{Style.RESET_ALL}")
        print(f"Skipped (dry run): {Fore.YELLOW}{self.stats['skipped']}{Style.RESET_ALL}")
        
        if self.stats['errors']:
            print(f"\n{Fore.RED}Errors encountered:{Style.RESET_ALL}")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error['chat_name']} (msg {error['message_id']}): {error['error']}")
            
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
    
    def save_error_report(self, output_file: str = None) -> str:
        """Save detailed error report to CSV."""
        if not self.stats['errors']:
            return ""
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/deletion_errors_{timestamp}.csv"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        errors_df = pd.DataFrame(self.stats['errors'])
        errors_df.to_csv(output_path, index=False, encoding='utf-8')
        
        self.logger.info(f"Error report saved to: {output_path}")
        return str(output_path)


async def main():
    """Example usage of the Telegram deleter."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Delete Telegram messages using Telethon')
    parser.add_argument('messages_csv', help='CSV file with messages to delete')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run mode (default)')
    parser.add_argument('--execute', action='store_true', help='Actually delete messages (overrides dry-run)')
    parser.add_argument('--batch-size', type=int, default=100, help='Messages per batch')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between batches (seconds)')
    
    args = parser.parse_args()
    
    # Load configuration
    from config import Config
    Config.validate()
    
    # Determine if this is a dry run
    dry_run = not args.execute if args.execute else args.dry_run
    
    if dry_run:
        print(f"{Fore.YELLOW}DRY RUN MODE - No messages will actually be deleted{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}LIVE MODE - Messages will be permanently deleted!{Style.RESET_ALL}")
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    # Load messages to delete
    messages_df = pd.read_csv(args.messages_csv)
    print(f"Loaded {len(messages_df)} messages to {'simulate deletion' if dry_run else 'delete'}")
    
    # Initialize deleter
    deleter = TelegramDeleter(
        Config.API_ID,
        Config.API_HASH,
        Config.PHONE_NUMBER,
        Config.SESSION_NAME
    )
    
    try:
        # Connect to Telegram
        if not await deleter.connect():
            print("Failed to connect to Telegram")
            return
        
        # Delete messages
        stats = await deleter.delete_messages_batch(
            messages_df,
            dry_run=dry_run,
            batch_size=args.batch_size,
            delay_between_batches=args.delay
        )
        
        # Print results
        deleter.print_statistics()
        
        # Save error report if there were errors
        if stats['errors']:
            deleter.save_error_report()
    
    finally:
        await deleter.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
