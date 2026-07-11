#!/usr/bin/env python3
"""
LCxRExOC - TELEGRAM BOT INTEGRATION
Full reporting bot with category selection
"""
import requests
import random
import time
import threading
import json
import hashlib
import re
import os
import sys
from fake_useragent import UserAgent
from datetime import datetime, timedelta
import phonenumbers
from phonenumbers import carrier, timezone, geocoder

# ============ BOT CONFIGURATION ============
BOT_TOKEN = "8666412239:AAHPrLPL0jSAaeA3hKKOlUXierSXtjf70MA"
OWNER_ID = "8935807032"

class TelegramFreezerBot:
    def __init__(self, token, owner_id):
        self.token = token
        self.owner_id = int(owner_id)
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.ua = UserAgent()
        self.session = requests.Session()
        self.offset = 0
        self.running = True
        self.current_target = None
        self.report_type = "child_porn"
        self.target_type = "channel"
        self.report_count = 0
        self.successful_reports = 0
        self.failed_reports = 0
        self.accounts = []
        self.detections = []
        self.logs_data = []
        self.is_freezing = False
        
        # ============ REPORT CATEGORIES ============
        self.report_configs = {
            "child_porn": {
                "name": "🚨 CHILD ABUSE",
                "reason": "child_abuse",
                "severity": "CRITICAL",
                "keywords": [
                    r'(?i)child\s*(porn|sex|abuse|exploit)',
                    r'(?i)minor\s*(nude|naked|sex)',
                    r'(?i)under\s*age\s*(sex|nude)',
                    r'(?i)teen\s*(porn|sex|nude)',
                    r'(?i)cp\s*(content|videos|links)',
                    r'(?i)pedo|pedophile',
                    r'(?i)lolita\s*(porn|sex)',
                    r'(?i)jailbait',
                    r'(?i)preteen\s*(sex|nude)',
                    r'(?i)kids\s*(sex|porn|nude)',
                ],
                "template": """
URGENT: Child Exploitation Material Detected

Target: @{target}
Type: Child Sexual Abuse Material
Severity: CRITICAL

Detected Content:
{detections}

ACTION REQUIRED:
- IMMEDIATE ACCOUNT BAN
- NOTIFY LAW ENFORCEMENT
"""
            },
            "hacking_mods": {
                "name": "🔧 HACKING/MODS",
                "reason": "malware",
                "severity": "HIGH",
                "keywords": [
                    r'(?i)mod\s*apk',
                    r'(?i)hack\s*(tool|software|download)',
                    r'(?i)esp\s*(hack|cheat|mod)',
                    r'(?i)aimbot',
                    r'(?i)wallhack',
                    r'(?i)triggerbot',
                    r'(?i)cheat\s*(engine|menu)',
                    r'(?i)cracked\s*(apk|game)',
                    r'(?i)unlimited\s*(money|gems|diamonds)',
                ],
                "template": """
URGENT: Malware/Hacking Tools Distribution

Target: @{target}
Type: Hacking Tools, Mods, Malware
Severity: HIGH

Detected Content:
{detections}

ACTION REQUIRED:
- Account suspension
- Investigate for malware
"""
            },
            "illegal_goods": {
                "name": "🚫 ILLEGAL GOODS",
                "reason": "illegal_goods",
                "severity": "HIGH",
                "keywords": [
                    r'(?i)drugs?\s*(sale|deal|buy)',
                    r'(?i)weapons?\s*(sale|deal|buy)',
                    r'(?i)illegal\s*(goods|items)',
                    r'(?i)black\s*market',
                    r'(?i)dark\s*web\s*(links|market)',
                ],
                "template": """
URGENT: Illegal Goods Distribution

Target: @{target}
Type: Illegal Goods/Products
Severity: HIGH

Detected Content:
{detections}

ACTION REQUIRED:
- Account ban
- Notify authorities
"""
            },
            "spam_scam": {
                "name": "📱 SPAM/SCAM",
                "reason": "spam",
                "severity": "MEDIUM",
                "keywords": [
                    r'(?i)earn\s*money\s*(fast|quick)',
                    r'(?i)get\s*rich\s*quick',
                    r'(?i)free\s*(money|gift|prize)',
                    r'(?i)bitcoin\s*(investment|mining)',
                    r'(?i)pyramid\s*scheme',
                ],
                "template": """
Spam/Scam Activity Detected

Target: @{target}
Type: Spam/Scam Content
Severity: MEDIUM

Detected Content:
{detections}

ACTION REQUIRED:
- Content removal
- Account warning
"""
            },
            "violence": {
                "name": "💀 VIOLENCE",
                "reason": "violence",
                "severity": "HIGH",
                "keywords": [
                    r'(?i)violence|violent',
                    r'(?i)death\s*threat',
                    r'(?i)kill\s*(someone|people)',
                    r'(?i)murder|homicide',
                    r'(?i)blood|gore',
                ],
                "template": """
URGENT: Violence/Threat Content Detected

Target: @{target}
Type: Violence/Threats
Severity: HIGH

Detected Content:
{detections}

ACTION REQUIRED:
- Account suspension
- Notify authorities
"""
            },
            "terrorism": {
                "name": "💣 TERRORISM",
                "reason": "terrorism",
                "severity": "CRITICAL",
                "keywords": [
                    r'(?i)terror|terrorism|terrorist',
                    r'(?i)isis|islamic\s*state',
                    r'(?i)bomb|explosive',
                    r'(?i)jihad',
                ],
                "template": """
URGENT: Terrorist Activity Detected

Target: @{target}
Type: Terrorism
Severity: CRITICAL

Detected Content:
{detections}

ACTION REQUIRED:
- IMMEDIATE BAN
- NOTIFY INTERPOL
"""
            },
            "adult_content": {
                "name": "🔞 ADULT CONTENT",
                "reason": "pornography",
                "severity": "MEDIUM",
                "keywords": [
                    r'(?i)sex\s*(video|chat|cam)',
                    r'(?i)nude\s*(video|pic|photo)',
                    r'(?i)porn\s*(video|link)',
                    r'(?i)xxx\s*(video|content)',
                    r'(?i)nsfw',
                ],
                "template": """
Adult Content Detected

Target: @{target}
Type: Adult/Pornography
Severity: MEDIUM

Detected Content:
{detections}

ACTION REQUIRED:
- Content removal
- Age restriction
"""
            }
        }
        
        self.report_keys = list(self.report_configs.keys())
        
        # ============ ENDPOINTS ============
        self.endpoints = [
            "https://web.telegram.org/api/report",
            "https://web.telegram.org/api/report_peer",
            "https://web.telegram.org/api/messages/report",
            "https://web.telegram.org/api/messages/report_spam",
        ]
        
        self.trigger_keywords = [
            "child sexual abuse material",
            "CSAM distribution",
            "minor exploitation",
            "pedophile network",
            "child trafficking",
            "terrorist activity",
            "illegal weapons trading",
            "drug trafficking",
        ]
        
        self.session_ids = [hashlib.md5(str(random.random()).encode()).hexdigest()[:16] for _ in range(100)]
        
        print(f"[+] Telegram Freezer Bot Started")
        print(f"[+] Owner ID: {self.owner_id}")
        print(f"[+] Categories: {', '.join(self.report_configs.keys())}")
        print("[+] Waiting for commands...")
    
    # ============ TELEGRAM BOT METHODS ============
    
    def send_message(self, chat_id, text, parse_mode=None):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            requests.post(url, json=payload, timeout=10)
        except:
            pass
    
    def send_menu(self, chat_id):
        menu = f"""
🤖 <b>TELEGRAM FREEZER BOT v2.0</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📋 COMMANDS:</b>
/start - Show this menu
/scan @username - Scan target
/freeze @username - Freeze target
/status - Current status
/stop - Stop operation
/category - Change report type
/targettype - Channel or User ID
/help - Help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🎯 CURRENT SETTINGS:</b>
Target: {self.current_target or 'None'}
Category: {self.report_configs.get(self.report_type, {}).get('name', 'None')}
Target Type: {self.target_type.upper()}
Reports Sent: {self.report_count}
Status: {'🟢 Running' if self.is_freezing else '🔴 Idle'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📌 USAGE:</b>
1. /category - Select report reason
2. /targettype - Select channel or ID
3. /scan @user - Scan for content
4. /freeze @user - Start freezing
"""
        self.send_message(chat_id, menu, parse_mode="HTML")
    
    def send_category_menu(self, chat_id):
        text = "📋 <b>SELECT REPORT CATEGORY</b>\n\n"
        for key, config in self.report_configs.items():
            text += f"<b>{key}</b> - {config['name']} [{config['severity']}]\n"
        text += "\n<b>Reply with category name:</b>\nExample: <code>child_porn</code>"
        self.send_message(chat_id, text, parse_mode="HTML")
    
    def send_targettype_menu(self, chat_id):
        text = """
📋 <b>SELECT TARGET TYPE</b>

<b>channel</b> - Scan posts & content
<b>id</b> - Scan logs & activity

Reply with: <code>channel</code> or <code>id</code>
"""
        self.send_message(chat_id, text, parse_mode="HTML")
    
    # ============ REPORTING METHODS ============
    
    def generate_report_text(self, category):
        keyword = random.choice(self.trigger_keywords)
        templates = [
            f"URGENT: This account is distributing {keyword}. Immediate ban required.",
            f"EMERGENCY: {keyword} detected. Take action immediately.",
            f"CRITICAL: User involved in {keyword}. Ban this account now.",
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
        
        config = self.report_configs.get(category, self.report_configs["child_porn"])
        reason = config["reason"]
        report_text = self.generate_report_text(category)
        
        payload = {
            "peer": target,
            "report_reason": reason,
            "message": report_text[:200],
            "report_type": "user" if self.target_type == "id" else "channel",
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
    
    # ============ SCANNING METHODS ============
    
    def scan_target_content(self, target):
        """Simple scan using web scraping"""
        detections = []
        try:
            # Try to fetch public page
            url = f"https://t.me/s/{target}"
            response = self.session.get(url, headers={"User-Agent": self.ua.random}, timeout=15)
            
            if response.status_code == 200:
                text = response.text
                
                # Check all categories
                for cat_key, config in self.report_configs.items():
                    for pattern in config["keywords"]:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            detections.append({
                                "category": cat_key,
                                "name": config["name"],
                                "pattern": pattern,
                                "matches": matches,
                                "severity": config["severity"]
                            })
            
            return detections
        except Exception as e:
            print(f"[-] Scan error: {e}")
            return []
    
    # ============ FREEZING WORKER ============
    
    def freeze_worker(self, target, category, reports, chat_id):
        success = 0
        fail = 0
        self.is_freezing = True
        
        for i in range(reports):
            if not self.running:
                break
            
            result = self.send_report(target, category)
            if result:
                success += 1
                self.report_count += 1
            else:
                fail += 1
            
            if (i + 1) % 10 == 0:
                self.send_message(chat_id, f"""
📊 <b>Progress:</b> {i+1}/{reports}
✅ Success: {success}
❌ Failed: {fail}
""", parse_mode="HTML")
            
            time.sleep(random.uniform(0.3, 0.8))
            
            if i % random.randint(3, 5) == 0:
                time.sleep(random.uniform(2, 5))
        
        self.is_freezing = False
        
        if success > 0:
            self.send_message(chat_id, f"""
✅ <b>FREEZE COMPLETE!</b>

🎯 Target: @{target}
📋 Category: {self.report_configs.get(category, {}).get('name', 'Unknown')}
✅ Success: {success}
❌ Failed: {fail}
📊 Total Reports: {self.report_count}

<b>Account will be banned within 10-30 minutes.</b>
""", parse_mode="HTML")
        else:
            self.send_message(chat_id, "❌ All reports failed. Try changing category.")
    
    # ============ COMMAND HANDLERS ============
    
    def start_freezing(self, chat_id, target):
        if not target or not target.startswith("@"):
            self.send_message(chat_id, "❌ Use: /freeze @username")
            return
        
        self.current_target = target
        self.running = True
        self.report_count = 0
        reports = 500
        
        self.send_message(chat_id, f"""
🚨 <b>FREEZING STARTED</b>

🎯 Target: {target}
📋 Category: {self.report_configs.get(self.report_type, {}).get('name', 'Unknown')}
📊 Reports: {reports}
⏱️ Estimated Time: 10-15 minutes

<b>⚠️ Account will be banned within 10-30 minutes.</b>
""", parse_mode="HTML")
        
        thread = threading.Thread(
            target=self.freeze_worker,
            args=(target, self.report_type, reports, chat_id)
        )
        thread.daemon = True
        thread.start()
    
    def start_scan(self, chat_id, target):
        if not target or not target.startswith("@"):
            self.send_message(chat_id, "❌ Use: /scan @username")
            return
        
        self.send_message(chat_id, f"🔍 Scanning @{target}...")
        
        detections = self.scan_target_content(target)
        
        if detections:
            result = f"🔍 <b>SCAN RESULTS FOR @{target}</b>\n\n"
            for det in detections[:10]:
                result += f"• {det['name']} [{det['severity']}]\n"
                result += f"  Pattern: {det['pattern']}\n"
            result += f"\nTotal Detections: {len(detections)}"
            self.send_message(chat_id, result, parse_mode="HTML")
        else:
            self.send_message(chat_id, f"✅ No violations detected in @{target}")
    
    def handle_command(self, chat_id, text):
        if chat_id != self.owner_id:
            self.send_message(chat_id, "❌ Unauthorized. This bot is private.")
            return
        
        text = text.strip()
        
        if text == "/start":
            self.send_menu(chat_id)
        
        elif text == "/menu":
            self.send_menu(chat_id)
        
        elif text == "/help":
            help_text = """
📖 <b>HELP</b>

/freeze @username - Freeze target
/scan @username - Scan target
/status - Show status
/stop - Stop operation
/category - Change report type
/targettype - Channel or ID mode

<b>Categories:</b>
child_porn - 🚨 Child Abuse
hacking_mods - 🔧 Hacking/Mods
illegal_goods - 🚫 Illegal Goods
spam_scam - 📱 Spam/Scam
violence - 💀 Violence
terrorism - 💣 Terrorism
adult_content - 🔞 Adult Content
"""
            self.send_message(chat_id, help_text, parse_mode="HTML")
        
        elif text == "/status":
            status = f"""
📊 <b>STATUS</b>

🎯 Target: {self.current_target or 'None'}
📋 Category: {self.report_configs.get(self.report_type, {}).get('name', 'None')}
📌 Target Type: {self.target_type.upper()}
📊 Reports: {self.report_count}
🔄 Running: {'✅ Yes' if self.is_freezing else '❌ No'}
"""
            self.send_message(chat_id, status, parse_mode="HTML")
        
        elif text == "/stop":
            self.running = False
            self.is_freezing = False
            self.send_message(chat_id, "🛑 Stopped all operations.")
        
        elif text == "/category":
            self.send_category_menu(chat_id)
        
        elif text == "/targettype":
            self.send_targettype_menu(chat_id)
        
        elif text.startswith("/freeze"):
            parts = text.split(" ")
            if len(parts) >= 2:
                target = parts[1].strip()
                if not target.startswith("@"):
                    target = "@" + target
                self.start_freezing(chat_id, target)
            else:
                self.send_message(chat_id, "❌ /freeze @username")
        
        elif text.startswith("/scan"):
            parts = text.split(" ")
            if len(parts) >= 2:
                target = parts[1].strip()
                if not target.startswith("@"):
                    target = "@" + target
                self.start_scan(chat_id, target)
            else:
                self.send_message(chat_id, "❌ /scan @username")
        
        # Category selection
        elif text.lower() in self.report_configs:
            self.report_type = text.lower()
            self.send_message(chat_id, f"✅ Category changed to: {self.report_configs[text.lower()]['name']}")
            self.send_menu(chat_id)
        
        # Target type selection
        elif text.lower() in ["channel", "id"]:
            self.target_type = text.lower()
            self.send_message(chat_id, f"✅ Target type changed to: {text.upper()}")
            self.send_menu(chat_id)
        
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
        except:
            return False
    
    def run(self):
        while True:
            try:
                self.get_updates()
            except:
                time.sleep(2)

# ============ MAIN ============
if __name__ == "__main__":
    bot = TelegramFreezerBot(BOT_TOKEN, OWNER_ID)
    bot.run()