#!/usr/bin/env python3
"""
Card Processing Bot - Splitter + BIN Selection + Only Cards
Version: 2.0.0
"""

import os
import re
import time
import json
import shutil
import logging
import random
import string
from datetime import datetime
from pathlib import Path
import telebot
from telebot import types
import threading

# ==================== CONFIG ====================
BOT_TOKEN = "8815661182:AAHMa-UX5hH0dmqgvgPuMGOf5797psYg6hk"

# Required channels to join
REQUIRED_CHANNELS = [
    {"link": "https://t.me/GODFATHERCHECKER", "username": "@GODFATHERCHECKER"},
    {"link": "https://t.me/+z2YaHNRE8u5hZjFl", "username": "@GODFATHERCHECKER2"}
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('card_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# User sessions
user_sessions = {}

# Create directories
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# ==================== CHANNEL CHECK ====================

def check_user_channels(user_id):
    """
    Check if user has joined all required channels
    """
    try:
        for channel in REQUIRED_CHANNELS:
            try:
                # Try to get chat member status
                status = bot.get_chat_member(channel['username'], user_id).status
                if status not in ['member', 'administrator', 'creator']:
                    return False, channel['link']
            except:
                return False, channel['link']
        return True, None
    except Exception as e:
        logger.error(f"Channel check error: {str(e)}")
        return False, REQUIRED_CHANNELS[0]['link']

# ==================== CARD PROCESSOR ====================

class CardProcessor:
    def __init__(self):
        self.input_dir = "input"
        self.output_dir = "output"
        self.temp_dir = "temp"
    
    def split_file(self, input_file, lines_per_file=10000):
        """
        Option 1: Split file into multiple files with specified lines
        """
        results = []
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            file_count = (total_lines + lines_per_file - 1) // lines_per_file
            
            base_name = os.path.basename(input_file).split('.')[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for i in range(file_count):
                start = i * lines_per_file
                end = min((i + 1) * lines_per_file, total_lines)
                chunk = lines[start:end]
                
                output_file = os.path.join(self.output_dir, f"{base_name}_part_{i+1}_of_{file_count}_{timestamp}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.writelines(chunk)
                
                results.append({
                    'file': output_file,
                    'lines': len(chunk),
                    'part': i+1,
                    'total': file_count
                })
            
            return {
                'success': True,
                'total_lines': total_lines,
                'file_count': file_count,
                'files': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def select_by_bin(self, input_file, bin_list):
        """
        Option 2: Select cards by BIN from a list
        """
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            bins = [b.strip() for b in bin_list.split(',') if b.strip()]
            
            matched_cards = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to extract card number from line
                card_match = re.search(r'\b(\d{15,16})\b', line)
                if card_match:
                    card_number = card_match.group(1)
                    
                    for target_bin in bins:
                        if card_number.startswith(target_bin):
                            matched_cards.append(line)
                            break
            
            if matched_cards:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(self.output_dir, f"bin_selected_{timestamp}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(matched_cards))
                
                return {
                    'success': True,
                    'total_cards': len(matched_cards),
                    'output_file': output_file,
                    'sample': matched_cards[:5]
                }
            else:
                return {
                    'success': False,
                    'error': 'No cards found matching the BIN(s)'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_only_cards(self, input_file):
        """
        Option 3: Extract only card number, expiry, CVV
        """
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            cleaned_cards = []
            
            # Common patterns for card data
            patterns = [
                # Card|MM|YY|CVV
                r'(\d{15,16})\s*[|,;:\t]\s*(\d{2})\s*[|,;:\t]\s*(\d{2})\s*[|,;:\t]\s*(\d{3,4})',
                # Card MM/YY CVV
                r'(\d{15,16})\s+(\d{2})\s*[/-]\s*(\d{2})\s+(\d{3,4})',
                # Card MM/YY/CVV
                r'(\d{15,16})\s*[/-]\s*(\d{2})\s*[/-]\s*(\d{2})\s*[/-]\s*(\d{3,4})',
                # Card with spaces
                r'(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{4})\s+(\d{2})\s*[/-]\s*(\d{2})\s+(\d{3,4})',
                # Simple card number then expiry then cvv
                r'(\d{15,16})\s*[,;:\t]\s*(\d{2})\s*[,;:\t]\s*(\d{2,4})\s*[,;:\t]\s*(\d{3,4})',
            ]
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                card_found = False
                
                # Try each pattern
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        groups = match.groups()
                        if len(groups) == 4:
                            card = groups[0]
                            month = groups[1]
                            year = groups[2]
                            cvv = groups[3]
                            # Fix year format
                            if len(year) == 2:
                                year = "20" + year
                            cleaned_cards.append(f"{card}|{month}|{year}|{cvv}")
                            card_found = True
                            break
                        elif len(groups) == 7:
                            # Card with spaces format
                            card = groups[0] + groups[1] + groups[2] + groups[3]
                            month = groups[4]
                            year = groups[5]
                            cvv = groups[6]
                            if len(year) == 2:
                                year = "20" + year
                            cleaned_cards.append(f"{card}|{month}|{year}|{cvv}")
                            card_found = True
                            break
                
                # Try extracting with simple regex if pattern failed
                if not card_found:
                    card_match = re.search(r'\b(\d{15,16})\b', line)
                    expiry_match = re.search(r'(\d{2})\s*[/-]\s*(\d{2,4})', line)
                    cvv_match = re.search(r'\b(\d{3,4})\b', line)
                    
                    if card_match and expiry_match and cvv_match:
                        card = card_match.group(1)
                        month = expiry_match.group(1)
                        year = expiry_match.group(2)
                        cvv = cvv_match.group(1)
                        if len(year) == 2:
                            year = "20" + year
                        cleaned_cards.append(f"{card}|{month}|{year}|{cvv}")
            
            if cleaned_cards:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(self.output_dir, f"only_cards_{timestamp}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(cleaned_cards))
                
                return {
                    'success': True,
                    'total_cards': len(cleaned_cards),
                    'output_file': output_file,
                    'sample': cleaned_cards[:5]
                }
            else:
                return {
                    'success': False,
                    'error': 'No valid card data found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

processor = CardProcessor()

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Welcome message with channel requirement"""
    user_id = message.from_user.id
    
    # Check if user has joined required channels
    joined, channel_link = check_user_channels(user_id)
    
    if not joined:
        join_text = """
⚠️ **Please join our channels first to use this bot!**

**Step 1:** Join these channels:
1️⃣ [GODFATHER CHECKER](https://t.me/GODFATHERCHECKER)
2️⃣ [SECOND CHANNEL](https://t.me/+z2YaHNRE8u5hZjFl)

**Step 2:** After joining, click /start again

📌 *This is required to prevent abuse of the bot.*
"""
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/GODFATHERCHECKER")
        btn2 = types.InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+z2YaHNRE8u5hZjFl")
        btn3 = types.InlineKeyboardButton("✅ Joined - Check Now", callback_data="check_joined")
        markup.add(btn1, btn2)
        markup.add(btn3)
        
        bot.reply_to(message, join_text, reply_markup=markup, parse_mode='Markdown')
        return
    
    welcome_text = """
💳 **Card Processing Bot**

**Available Operations:**

1️⃣ **SPLITTER** - Split large card files into smaller chunks
   Usage: `/split 10000` (after uploading file)

2️⃣ **BIN SELECTION** - Filter cards by specific BIN numbers
   Usage: `/bin 414720,414721,414722` (after uploading file)

3️⃣ **ONLY CARDS** - Extract only card|month|year|cvv
   Usage: `/cards` (after uploading file)

**How to use:**
1. Upload a .txt file with card data
2. Use one of the commands above
3. Download the processed file

**Commands:**
/start - Show this menu
/split [number] - Split file
/bin [bins] - Filter by BIN
/cards - Extract only card data
/help - Detailed help
/status - Check status
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 **Detailed Help**

**1. SPLITTER (/split [number])**
- Upload a card file
- Use: `/split 10000`
- Bot splits into files of 10,000 lines each

**2. BIN SELECTION (/bin [bins])**
- Upload a card file
- Use: `/bin 414720,414721`
- Bot extracts all cards starting with those BINs

**3. ONLY CARDS (/cards)**
- Upload a messy card file
- Use: `/cards`
- Bot extracts only card|month|year|cvv

**Supported Formats:**
- Card|MM|YY|CVV
- Card MM/YY CVV
- Card with spaces
- Mixed formats

**File Limits:**
- Maximum file size: 50MB
- Maximum lines: 1,000,000
"""

@bot.message_handler(commands=['split'])
def cmd_split(message):
    """Handle /split command"""
    user_id = message.from_user.id
    
    # Check channels
    joined, _ = check_user_channels(user_id)
    if not joined:
        bot.reply_to(message, "⚠️ Please join required channels first. Use /start")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Please specify number of lines per file.\nExample: `/split 10000`", parse_mode='Markdown')
        return
    
    try:
        lines_per_file = int(parts[1])
        if lines_per_file < 1:
            bot.reply_to(message, "❌ Please enter a number greater than 0")
            return
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number")
        return
    
    user_sessions[message.chat.id] = {
        'action': 'split',
        'lines_per_file': lines_per_file,
        'step': 'waiting_for_file'
    }
    
    bot.reply_to(
        message,
        f"📤 **Upload a .txt file to split into {lines_per_file} lines per file**",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['bin'])
def cmd_bin(message):
    """Handle /bin command"""
    user_id = message.from_user.id
    
    # Check channels
    joined, _ = check_user_channels(user_id)
    if not joined:
        bot.reply_to(message, "⚠️ Please join required channels first. Use /start")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Please specify BINs.\nExample: `/bin 414720,414721,414722`", parse_mode='Markdown')
        return
    
    bin_list = parts[1]
    user_sessions[message.chat.id] = {
        'action': 'bin',
        'bin_list': bin_list,
        'step': 'waiting_for_file'
    }
    
    bot.reply_to(
        message,
        f"📤 **Upload a .txt file to filter by BIN:**\n`{bin_list}`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['cards'])
def cmd_cards(message):
    """Handle /cards command"""
    user_id = message.from_user.id
    
    # Check channels
    joined, _ = check_user_channels(user_id)
    if not joined:
        bot.reply_to(message, "⚠️ Please join required channels first. Use /start")
        return
    
    user_sessions[message.chat.id] = {
        'action': 'cards',
        'step': 'waiting_for_file'
    }
    
    bot.reply_to(
        message,
        "📤 **Upload a .txt file to extract only card|month|year|cvv**",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Handle file uploads"""
    try:
        chat_id = message.chat.id
        
        # Check channels
        joined, _ = check_user_channels(message.from_user.id)
        if not joined:
            bot.reply_to(message, "⚠️ Please join required channels first. Use /start")
            return
        
        if chat_id not in user_sessions:
            bot.reply_to(message, "❌ Please use a command first: /split, /bin, or /cards")
            return
        
        session = user_sessions[chat_id]
        action = session.get('action')
        
        if not action:
            bot.reply_to(message, "❌ Please use a command first")
            return
        
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_file = os.path.join("input", f"{chat_id}_{timestamp}.txt")
        with open(input_file, 'wb') as f:
            f.write(downloaded_file)
        
        # Count lines
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = sum(1 for _ in f)
        
        session['input_file'] = input_file
        
        bot.reply_to(
            message,
            f"✅ File uploaded: {message.document.file_name}\n"
            f"📊 Total lines: {line_count}\n\n"
            f"⏳ Processing {action}... Please wait."
        )
        
        # Process based on action
        if action == 'split':
            process_split(message, session)
        elif action == 'bin':
            process_bin(message, session)
        elif action == 'cards':
            process_cards(message, session)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        logger.error(f"Error in handle_document: {str(e)}")

def process_split(message, session):
    """Process split operation"""
    try:
        chat_id = message.chat.id
        input_file = session.get('input_file')
        lines_per_file = session.get('lines_per_file', 10000)
        
        if not input_file:
            bot.reply_to(message, "❌ No file found")
            return
        
        result = processor.split_file(input_file, lines_per_file)
        
        if result['success']:
            response = f"✅ **SPLIT COMPLETE!**\n\n"
            response += f"Total lines: {result['total_lines']}\n"
            response += f"Files created: {result['file_count']}\n\n"
            response += "**Files:**\n"
            
            for file_info in result['files']:
                response += f"• {os.path.basename(file_info['file'])} - {file_info['lines']} lines\n"
            
            bot.reply_to(message, response, parse_mode='Markdown')
            
            # Send files
            for file_info in result['files'][:10]:
                with open(file_info['file'], 'rb') as f:
                    bot.send_document(chat_id, f)
            
            if result['file_count'] > 10:
                bot.reply_to(message, f"📦 Plus {result['file_count'] - 10} more files in output directory")
            
            # Cleanup
            session.clear()
            
        else:
            bot.reply_to(message, f"❌ Error: {result['error']}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_bin(message, session):
    """Process bin selection operation"""
    try:
        chat_id = message.chat.id
        input_file = session.get('input_file')
        bin_list = session.get('bin_list', '')
        
        if not input_file:
            bot.reply_to(message, "❌ No file found")
            return
        
        result = processor.select_by_bin(input_file, bin_list)
        
        if result['success']:
            response = f"✅ **BIN SELECTION COMPLETE!**\n\n"
            response += f"Cards found: {result['total_cards']}\n"
            response += f"Output: {os.path.basename(result['output_file'])}\n\n"
            response += "**Sample:**\n"
            for sample in result['sample']:
                response += f"• {sample}\n"
            
            bot.reply_to(message, response, parse_mode='Markdown')
            
            with open(result['output_file'], 'rb') as f:
                bot.send_document(chat_id, f)
            
            session.clear()
            
        else:
            bot.reply_to(message, f"❌ Error: {result['error']}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def process_cards(message, session):
    """Process only cards extraction operation"""
    try:
        chat_id = message.chat.id
        input_file = session.get('input_file')
        
        if not input_file:
            bot.reply_to(message, "❌ No file found")
            return
        
        result = processor.extract_only_cards(input_file)
        
        if result['success']:
            response = f"✅ **ONLY CARDS COMPLETE!**\n\n"
            response += f"Cards extracted: {result['total_cards']}\n"
            response += f"Output: {os.path.basename(result['output_file'])}\n\n"
            response += "**Sample (Card|MM|YYYY|CVV):**\n"
            for sample in result['sample']:
                response += f"• {sample}\n"
            
            bot.reply_to(message, response, parse_mode='Markdown')
            
            with open(result['output_file'], 'rb') as f:
                bot.send_document(chat_id, f)
            
            session.clear()
            
        else:
            bot.reply_to(message, f"❌ Error: {result['error']}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# ==================== CALLBACK HANDLERS ====================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle callback queries"""
    try:
        if call.data == "check_joined":
            user_id = call.from_user.id
            joined, _ = check_user_channels(user_id)
            
            if joined:
                bot.answer_callback_query(call.id, "✅ You have joined all channels!")
                bot.edit_message_text(
                    "✅ **Access Granted!**\n\nYou can now use the bot.\nUse /start to begin.",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                bot.answer_callback_query(call.id, "❌ Please join both channels first!")
                
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")

# ==================== STATUS COMMAND ====================

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Check bot status"""
    status_text = """
📊 **Bot Status**

✅ **Online**
📅 Version: 2.0.0

**Features:**
1️⃣ SPLITTER - ✅ Active
2️⃣ BIN SELECTION - ✅ Active
3️⃣ ONLY CARDS - ✅ Active

**File Limits:**
- Max file size: 50MB
- Max lines: 1,000,000

**Channel Check:** ✅ Active
"""
    bot.reply_to(message, status_text, parse_mode='Markdown')

# ==================== DEFAULT HANDLER ====================

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Handle unknown commands"""
    bot.reply_to(
        message,
        "❓ Unknown command.\n\n"
        "Use /help to see available commands.",
        parse_mode='Markdown'
    )

# ==================== MAIN ====================

def main():
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   CARD PROCESSING BOT v2.0                   ║
    ║   - SPLITTER                                ║
    ║   - BIN SELECTION                           ║
    ║   - ONLY CARDS                              ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    print(f"✅ Bot token: {BOT_TOKEN[:10]}...")
    print(f"✅ Required channels: {len(REQUIRED_CHANNELS)}")
    print(f"✅ Bot starting...")
    
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()