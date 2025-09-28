"""
JSON Analyzer for Telegram Export Data
Analyzes exported Telegram JSON data to find messages containing specified keywords.
"""
import json
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

class TelegramJSONAnalyzer:
    def __init__(self, export_file: str):
        """
        Initialize the analyzer with a Telegram JSON export file.
        
        Args:
            export_file: Path to the JSON export file
        """
        self.export_file = Path(export_file)
        self.data = None
        self.messages_df = None
        
    def load_export(self) -> Dict[str, Any]:
        """Load the JSON export data."""
        if not self.export_file.exists():
            raise FileNotFoundError(f"Export file not found: {self.export_file}")
        
        print(f"Loading Telegram export from: {self.export_file}")
        with open(self.export_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"Loaded {len(self.data.get('chats', {}).get('list', []))} chats")
        return self.data
    
    def extract_outgoing_messages(self) -> pd.DataFrame:
        """
        Extract all outgoing messages from the JSON export.
        Returns a DataFrame with message details.
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_export() first.")
        
        # Get user ID from personal information
        user_id = self.data.get('personal_information', {}).get('user_id')
        if not user_id:
            # Try to extract from first message if personal_information not available
            user_id = None
            for chat in self.data.get('chats', {}).get('list', []):
                for message in chat.get('messages', []):
                    if message.get('from_id', '').startswith('user'):
                        user_id = message.get('from_id')
                        break
                if user_id:
                    break
        
        if not user_id:
            print("⚠️  Warning: Could not determine user ID. Will try to detect outgoing messages by other means.")
        
        messages = []
        chats = self.data.get('chats', {}).get('list', [])
        
        for chat in chats:
            chat_id = chat.get('id')
            chat_name = chat.get('name', f"Chat_{chat_id}")
            chat_type = chat.get('type', 'unknown')
            
            # Process messages in this chat
            for message in chat.get('messages', []):
                # Check if this is an outgoing message
                is_outgoing = False
                
                # Method 1: Check for 'out' field (older format)
                if message.get('out', False):
                    is_outgoing = True
                
                # Method 2: Check if from_id matches user ID (newer format)
                elif user_id and message.get('from_id') == f"user{user_id}":
                    is_outgoing = True
                
                # Method 3: Check if from_id starts with 'user' and matches user ID
                elif user_id and message.get('from_id') == str(user_id):
                    is_outgoing = True
                
                # Method 4: Check if from field matches the user's name
                elif message.get('from') and message.get('from') == self.data.get('personal_information', {}).get('first_name', ''):
                    is_outgoing = True
                
                if is_outgoing:
                    # Handle text field which can be string or list
                    text_content = message.get('text', '')
                    if isinstance(text_content, list):
                        # Extract text from text entities
                        text_content = ' '.join([item.get('text', '') for item in text_content if isinstance(item, dict) and 'text' in item])
                    
                    msg_data = {
                        'chat_id': chat_id,
                        'chat_name': chat_name,
                        'chat_type': chat_type,
                        'message_id': message.get('id'),
                        'date': message.get('date_unixtime', message.get('date')),
                        'text': text_content,
                        'from_id': message.get('from_id'),
                        'from': message.get('from'),
                        'reply_to_message_id': message.get('reply_to_message_id'),
                    }
                    messages.append(msg_data)
        
        self.messages_df = pd.DataFrame(messages)
        
        # Convert date to datetime
        if not self.messages_df.empty:
            # Handle both unix timestamp and ISO date formats
            if self.messages_df['date'].dtype == 'object':
                # Try to convert unix timestamp first
                try:
                    self.messages_df['date'] = pd.to_datetime(self.messages_df['date'], unit='s')
                except:
                    # If that fails, try regular datetime parsing
                    self.messages_df['date'] = pd.to_datetime(self.messages_df['date'])
        
        print(f"Extracted {len(self.messages_df)} outgoing messages")
        return self.messages_df
    
    def find_messages_by_keywords(self, keywords: List[str], 
                                 case_sensitive: bool = False,
                                 whole_words: bool = True) -> pd.DataFrame:
        """
        Find messages containing any of the specified keywords.
        
        Args:
            keywords: List of regex patterns to search for
            case_sensitive: Whether search should be case sensitive
            whole_words: Whether to match whole words only
        
        Returns:
            DataFrame containing matching messages
        """
        if self.messages_df is None:
            raise ValueError("No messages loaded. Call extract_outgoing_messages() first.")
        
        if not keywords:
            return pd.DataFrame()
        
        # Combine keywords into a single regex pattern
        if whole_words:
            # Add word boundaries for whole word matching
            keyword_patterns = [rf'\b{kw}\b' for kw in keywords]
        else:
            keyword_patterns = keywords
        
        combined_pattern = '|'.join(keyword_patterns)
        
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(combined_pattern, flags)
        
        # Find matching messages
        matches = []
        for idx, row in self.messages_df.iterrows():
            text = str(row['text'])
            if pattern.search(text):
                # Find which keywords matched
                matched_keywords = []
                for kw in keywords:
                    if whole_words:
                        kw_pattern = rf'\b{kw}\b'
                    else:
                        kw_pattern = kw
                    
                    kw_flags = 0 if case_sensitive else re.IGNORECASE
                    if re.search(kw_pattern, text, kw_flags):
                        matched_keywords.append(kw)
                
                match_data = row.copy()
                match_data['matched_keywords'] = ', '.join(matched_keywords)
                matches.append(match_data)
        
        matches_df = pd.DataFrame(matches)
        print(f"Found {len(matches_df)} messages matching keywords: {', '.join(keywords)}")
        
        return matches_df
    
    def save_preview_csv(self, matches_df: pd.DataFrame, output_file: str = None) -> str:
        """
        Save matching messages to a CSV file for preview.
        
        Args:
            matches_df: DataFrame with matching messages
            output_file: Output file path (optional)
        
        Returns:
            Path to the saved file
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/keyword_matches_{timestamp}.csv"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Select relevant columns for preview
        preview_columns = [
            'chat_name', 'chat_type', 'message_id', 'date', 
            'text', 'matched_keywords'
        ]
        
        preview_df = matches_df[preview_columns].copy()
        preview_df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"Preview saved to: {output_path}")
        return str(output_path)
    
    def get_message_summary(self, matches_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get a summary of matching messages.
        
        Args:
            matches_df: DataFrame with matching messages
        
        Returns:
            Dictionary with summary statistics
        """
        if matches_df.empty:
            return {
                'total_matches': 0,
                'unique_chats': 0,
                'date_range': None,
                'keyword_counts': {}
            }
        
        summary = {
            'total_matches': len(matches_df),
            'unique_chats': matches_df['chat_name'].nunique(),
            'date_range': {
                'earliest': matches_df['date'].min(),
                'latest': matches_df['date'].max()
            }
        }
        
        # Count matches per keyword
        keyword_counts = {}
        for keywords_str in matches_df['matched_keywords']:
            for keyword in keywords_str.split(', '):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        summary['keyword_counts'] = keyword_counts
        
        return summary
    
    def print_summary(self, matches_df: pd.DataFrame):
        """Print a formatted summary of matching messages."""
        summary = self.get_message_summary(matches_df)
        
        print("\n" + "="*50)
        print("SEARCH RESULTS SUMMARY")
        print("="*50)
        print(f"Total messages found: {summary['total_matches']}")
        print(f"Unique chats: {summary['unique_chats']}")
        
        if summary['date_range']:
            print(f"Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        print("\nKeyword matches:")
        for keyword, count in summary['keyword_counts'].items():
            print(f"  - '{keyword}': {count} messages")
        
        if not matches_df.empty:
            print(f"\nChats with matches:")
            chat_counts = matches_df['chat_name'].value_counts()
            for chat, count in chat_counts.head(10).items():
                print(f"  - {chat}: {count} messages")
            
            if len(chat_counts) > 10:
                print(f"  ... and {len(chat_counts) - 10} more chats")


def main():
    """Example usage of the JSON analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Telegram JSON export for keyword matches')
    parser.add_argument('export_file', help='Path to Telegram JSON export file')
    parser.add_argument('--keywords', nargs='+', required=True, help='Keywords to search for')
    parser.add_argument('--case-sensitive', action='store_true', help='Case sensitive search')
    parser.add_argument('--whole-words', action='store_true', default=True, help='Match whole words only')
    parser.add_argument('--output', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = TelegramJSONAnalyzer(args.export_file)
    
    # Load and process data
    analyzer.load_export()
    analyzer.extract_outgoing_messages()
    
    # Find matches
    matches = analyzer.find_messages_by_keywords(
        args.keywords, 
        case_sensitive=args.case_sensitive,
        whole_words=args.whole_words
    )
    
    # Print summary
    analyzer.print_summary(matches)
    
    # Save preview
    if not matches.empty:
        analyzer.save_preview_csv(matches, args.output)
    else:
        print("No matching messages found.")


if __name__ == '__main__':
    main()
