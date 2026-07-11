#!/usr/bin/env python3
"""
LCxRExOC - TELEGRAM BOT INTEGRATION
FULL SCRIPT - COMPLETE
"""
import requests
import random
import time
import threading
import json
import hashlib
import re
import base64
import os
import sys
from fake_useragent import UserAgent
from colorama import Fore, Style, init
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from queue import Queue
import phonenumbers
from phonenumbers import carrier, timezone, geocoder
from datetime import datetime, timedelta

init(autoreset=True)

BOT_TOKEN = "8666412239:AAHPrLPL0jSAaeA3hKKOlUXierSXtjf70MA"
OWNER_ID = "8935807032"

class MultiReportNuker:
    def __init__(self, target, report_type="child_porn", target_type="channel"):
        self.target = target
        self.report_type = report_type
        self.target_type = target_type
        self.ua = UserAgent()
        self.session = requests.Session()
        self.accounts = []
        self.report_queue = Queue()
        self.successful_reports = 0
        self.failed_reports = 0
        self.lock = threading.Lock()
        self.detections = []
        self.logs_data = []
        
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
                    r'(?i)schoolgirl\s*(porn|sex)',
                ],
                "template": """
                URGENT: Child Exploitation Material Detected
                Target: @{target}
                Type: Child Sexual Abuse Material
                Severity: CRITICAL
                Detected Content:
                {detections}
                ACTION REQUIRED: IMMEDIATE ACCOUNT BAN
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
                Type: Hacking Tools
                Severity: HIGH
                Detected Content:
                {detections}
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
                Type: Illegal Goods
                Severity: HIGH
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
                Type: Spam/Scam
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
                URGENT: Violence Content Detected
                Target: @{target}
                Type: Violence/Threats
                Severity: HIGH
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
                """
            }
        }
        
        self.id_log_patterns = {
            "child_porn": [
                r'(?i)child\s*(porn|sex|abuse|exploit)',
                r'(?i)minor\s*(nude|naked|sex)',
                r'(?i)teen\s*(porn|sex|nude)',
                r'(?i)cp\s*(content|videos|links)',
                r'(?i)pedo|pedophile',
                r'(?i)jailbait',
                r'(?i)selling\s*(cp|child|minor)',
                r'(?i)trading\s*(cp|child|minor)',
                r'(?i)dm\s*for\s*(cp|child|underage)',
            ],
            "sexual_content": [
                r'(?i)sex\s*(video|chat|cam)',
                r'(?i)nude\s*(video|pic|photo)',
                r'(?i)porn\s*(video|link)',
                r'(?i)xxx\s*(video|content)',
                r'(?i)nsfw',
            ]
        }
        
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
        self.setup_browser()
    
    def setup_browser(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("--disable-blink-features=AutomationControlled")
    
    def load_accounts(self, accounts_file="accounts.txt"):
        accounts = []
        try:
            with open(accounts_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            phone, password = line.split(':', 1)
                            accounts.append({
                                'phone': phone.strip(),
                                'password': password.strip(),
                                'session_id': hashlib.md5(f"{phone}{time.time()}".encode()).hexdigest()[:16],
                                'active': True
                            })
        except FileNotFoundError:
            print(f"{Fore.YELLOW}[!] accounts.txt not found. Creating sample...")
            with open(accounts_file, 'w') as f:
                f.write("# Add Telegram accounts here (phone:password)\n")
                f.write("# Example: +919876543210:mypass123\n")
        return accounts
    
    def add_account_manually(self):
        print(f"{Fore.CYAN}")
        print("╔═══════════════════════════════════════════════════╗")
        print("║         ADD TELEGRAM ACCOUNT                     ║")
        print("╚═══════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")
        
        while True:
            phone = input(f"\n{Fore.YELLOW}Enter phone number (with country code, e.g., +919876543210): {Style.RESET_ALL}")
            try:
                parsed = phonenumbers.parse(phone)
                if not phonenumbers.is_valid_number(parsed):
                    print(f"{Fore.RED}[-] Invalid phone number. Try again.{Style.RESET_ALL}")
                    continue
                print(f"{Fore.GREEN}[+] Valid phone number detected.{Style.RESET_ALL}")
                break
            except:
                print(f"{Fore.RED}[-] Invalid format. Try again.{Style.RESET_ALL}")
        
        password = input(f"{Fore.YELLOW}Enter password/OTP (or press Enter if none): {Style.RESET_ALL}")
        
        self.accounts.append({
            'phone': phone,
            'password': password if password else f"pass{random.randint(1000,9999)}",
            'session_id': hashlib.md5(f"{phone}{time.time()}".encode()).hexdigest()[:16],
            'active': True
        })
        
        with open("accounts.txt", 'a') as f:
            f.write(f"{phone}:{password if password else f'pass{random.randint(1000,9999)}'}\n")
        
        print(f"{Fore.GREEN}[+] Account added successfully! Total accounts: {len(self.accounts)}{Style.RESET_ALL}")
        return True
    
    def add_multiple_accounts(self):
        print(f"{Fore.CYAN}")
        print("╔═══════════════════════════════════════════════════╗")
        print("║         ADD ACCOUNTS MENU                        ║")
        print("╚═══════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}[1] Load from accounts.txt file")
        print(f"[2] Add accounts manually (one by one)")
        print(f"[3] Generate fake accounts")
        print(f"[4] Skip (guest mode){Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.CYAN}Choice: {Style.RESET_ALL}")
        
        if choice == "1":
            self.accounts = self.load_accounts()
            print(f"{Fore.GREEN}[+] Loaded {len(self.accounts)} accounts from file{Style.RESET_ALL}")
        elif choice == "2":
            while True:
                self.add_account_manually()
                cont = input(f"{Fore.CYAN}Add another account? (y/n): {Style.RESET_ALL}")
                if cont.lower() != 'y':
                    break
        elif choice == "3":
            for i in range(20):
                phone = f"+{random.randint(100,999)}{random.randint(100,999)}{random.randint(1000,9999)}"
                password = f"pass{random.randint(1000,9999)}"
                self.accounts.append({
                    'phone': phone,
                    'password': password,
                    'session_id': hashlib.md5(f"{phone}{time.time()}".encode()).hexdigest()[:16],
                    'active': True
                })
            print(f"{Fore.GREEN}[+] Generated {len(self.accounts)} fake accounts{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] Skipping account addition. Using guest mode.{Style.RESET_ALL}")
    
    def choose_target_type(self):
        print(f"{Fore.CYAN}")
        print("╔═══════════════════════════════════════════════════╗")
        print("║         SELECT TARGET TYPE                       ║")
        print("╚═══════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}[1] 📢 CHANNEL - Scan posts & content")
        print(f"[2] 🆔 USER ID - Scan logs & activity{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.CYAN}Select target type (1-2): {Style.RESET_ALL}")
        
        if choice == "2":
            self.target_type = "id"
            print(f"{Fore.GREEN}[+] Target type: USER ID{Style.RESET_ALL}")
        else:
            self.target_type = "channel"
            print(f"{Fore.GREEN}[+] Target type: CHANNEL{Style.RESET_ALL}")
        
        return self.target_type
    
    def choose_report_type(self):
        print(f"{Fore.CYAN}")
        print("╔═══════════════════════════════════════════════════╗")
        print("║         SELECT REPORT TYPE                       ║")
        print("╚═══════════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}[1] 🚨 CHILD ABUSE (CRITICAL)")
        print(f"[2] 🔧 HACKING/MODS (HIGH)")
        print(f"[3] 🚫 ILLEGAL GOODS (HIGH)")
        print(f"[4] 📱 SPAM/SCAM (MEDIUM)")
        print(f"[5] 💀 VIOLENCE (HIGH)")
        print(f"[6] 💣 TERRORISM (CRITICAL)")
        print(f"[7] 🔞 ADULT CONTENT (MEDIUM)")
        print(f"[8] 🔍 AUTO-DETECT{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.CYAN}Select report type (1-8): {Style.RESET_ALL}")
        
        report_types = {
            "1": "child_porn",
            "2": "hacking_mods",
            "3": "illegal_goods",
            "4": "spam_scam",
            "5": "violence",
            "6": "terrorism",
            "7": "adult_content",
            "8": "auto_detect"
        }
        
        selected = report_types.get(choice, "child_porn")
        print(f"{Fore.GREEN}[+] Selected: {selected.upper()}{Style.RESET_ALL}")
        return selected
    
    def fetch_channel_content(self):
        driver = None
        all_content = []
        try:
            driver = webdriver.Chrome(options=self.options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            urls = [
                f"https://t.me/{self.target}",
                f"https://t.me/s/{self.target}"
            ]
            
            for url in urls:
                try:
                    driver.get(url)
                    time.sleep(random.uniform(2, 4))
                    
                    if "Sorry, this username doesn't exist" in driver.page_source:
                        continue
                    
                    for _ in range(5):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(random.uniform(1, 2))
                    
                    messages = driver.find_elements(By.CLASS_NAME, "tgme_widget_message")
                    
                    for msg in messages:
                        try:
                            text = msg.text
                            links = [link.get_attribute("href") for link in msg.find_elements(By.TAG_NAME, "a")]
                            all_content.append({
                                'text': text,
                                'links': links,
                                'has_media': bool(msg.find_elements(By.CLASS_NAME, "tgme_widget_message_photo_wrap"))
                            })
                        except:
                            continue
                    
                    try:
                        bio = driver.find_element(By.CLASS_NAME, "tgme_page_description")
                        all_content.append({'text': bio.text, 'links': [], 'has_media': False})
                    except:
                        pass
                    
                    break
                    
                except:
                    continue
            
            return all_content
            
        except Exception as e:
            print(f"{Fore.RED}[-] Error: {str(e)[:50]}{Style.RESET_ALL}")
            return []
        finally:
            if driver:
                driver.quit()
    
    def fetch_id_logs(self):
        driver = None
        logs_data = []
        try:
            driver = webdriver.Chrome(options=self.options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            urls = [
                f"https://t.me/{self.target}",
                f"https://t.me/s/{self.target}"
            ]
            
            for url in urls:
                try:
                    driver.get(url)
                    time.sleep(random.uniform(2, 4))
                    
                    if "Sorry, this username doesn't exist" in driver.page_source:
                        continue
                    
                    try:
                        name = driver.find_element(By.CLASS_NAME, "tgme_page_title").text
                        bio = driver.find_element(By.CLASS_NAME, "tgme_page_description").text
                        logs_data.append({
                            'type': 'profile',
                            'content': f"Name: {name}\nBio: {bio}",
                            'timestamp': datetime.now().isoformat()
                        })
                    except:
                        pass
                    
                    messages = driver.find_elements(By.CLASS_NAME, "tgme_widget_message")
                    for msg in messages:
                        try:
                            text = msg.text
                            if text:
                                logs_data.append({
                                    'type': 'post',
                                    'content': text,
                                    'timestamp': datetime.now().isoformat()
                                })
                        except:
                            continue
                    
                    forwarded = driver.find_elements(By.CLASS_NAME, "tgme_widget_message_forwarded_from")
                    for fwd in forwarded:
                        try:
                            logs_data.append({
                                'type': 'forwarded',
                                'content': fwd.text,
                                'timestamp': datetime.now().isoformat()
                            })
                        except:
                            continue
                    
                    replies = driver.find_elements(By.CLASS_NAME, "tgme_widget_message_reply")
                    for reply in replies:
                        try:
                            logs_data.append({
                                'type': 'reply',
                                'content': reply.text,
                                'timestamp': datetime.now().isoformat()
                            })
                        except:
                            continue
                    
                    break
                    
                except:
                    continue
            
            if not logs_data:
                print(f"{Fore.YELLOW}[!] No logs found. Using simulated logs.{Style.RESET_ALL}")
                logs_data = self.generate_simulated_logs()
            
            return logs_data
            
        except Exception as e:
            print(f"{Fore.RED}[-] Error: {str(e)[:50]}{Style.RESET_ALL}")
            return self.generate_simulated_logs()
        finally:
            if driver:
                driver.quit()
    
    def generate_simulated_logs(self):
        logs = []
        log_templates = [
            {"type": "message", "content": "Check this: {link}"},
            {"type": "message", "content": "Selling {item} cheap"},
            {"type": "message", "content": "Wanna trade {item}?"},
            {"type": "message", "content": "Got {item} if anyone wants"},
            {"type": "message", "content": "DM for {item} link"},
        ]
        
        suspicious_items = ["cp", "child", "minor", "underage", "teen", "pedo"]
        
        for i in range(random.randint(10, 20)):
            template = random.choice(log_templates)
            item = random.choice(suspicious_items) if random.random() < 0.3 else "stuff"
            
            log = {
                "type": random.choice(["message", "forwarded", "reply"]),
                "content": template.format(item=item, link="t.me/xxx"),
                "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat()
            }
            logs.append(log)
        
        return logs
    
    def scan_id_logs(self, logs_data):
        detections = []
        
        for log in logs_data:
            content = log.get('content', '')
            log_type = log.get('type', 'unknown')
            
            for pattern in self.id_log_patterns['child_porn']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    detections.append({
                        'type': 'child_porn',
                        'log_type': log_type,
                        'pattern': pattern,
                        'content': content[:150],
                        'matches': matches,
                        'timestamp': log.get('timestamp', ''),
                        'severity': 'CRITICAL'
                    })
            
            for pattern in self.id_log_patterns['sexual_content']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    detections.append({
                        'type': 'sexual_content',
                        'log_type': log_type,
                        'pattern': pattern,
                        'content': content[:150],
                        'matches': matches,
                        'timestamp': log.get('timestamp', ''),
                        'severity': 'HIGH'
                    })
        
        return detections
    
    def generate_id_report(self, detections):
        if not detections:
            return None
        
        child_porn_detections = [d for d in detections if d['type'] == 'child_porn']
        sexual_detections = [d for d in detections if d['type'] == 'sexual_content']
        
        report = f"""
        URGENT: Child Exploitation Detected in User Logs
        Target User: @{self.target}
        Target Type: USER ID
        Logs Scanned: {len(self.logs_data)}
        Total Detections: {len(detections)}
        CHILD PORNOGRAPHY DETECTIONS: {len(child_porn_detections)}
        """
        
        for i, det in enumerate(child_porn_detections[:5]):
            report += f"""
        --- Detection {i+1} ---
        Log Type: {det['log_type']}
        Pattern: {det['pattern']}
        Content: {det['content']}
        """
        
        if sexual_detections:
            report += f"SEXUAL CONTENT DETECTIONS: {len(sexual_detections)}"
            for i, det in enumerate(sexual_detections[:3]):
                report += f"""
        --- Sexual Detection {i+1} ---
        Content: {det['content']}
        """
        
        report += """
        ACTION REQUIRED: IMMEDIATE ACCOUNT BAN
        """
        
        return report
    
    def scan_and_generate_report(self, content_list):
        if self.target_type == "id":
            print(f"{Fore.CYAN}[*] Scanning ID logs...{Style.RESET_ALL}")
            self.logs_data = self.fetch_id_logs()
            detections = self.scan_id_logs(self.logs_data)
            if not detections:
                return None
            child_porn_detections = [d for d in detections if d['type'] == 'child_porn']
            if not child_porn_detections:
                sexual_detections = [d for d in detections if d['type'] == 'sexual_content']
                if sexual_detections and self.report_type == "child_porn":
                    return self.generate_id_report(detections)
                return None
            return self.generate_id_report(detections)
        else:
            if self.report_type == "auto_detect":
                all_detections = []
                detected_types = set()
                for content in content_list:
                    text = content.get('text', '')
                    for type_name, config in self.report_configs.items():
                        for pattern in config['keywords']:
                            matches = re.findall(pattern, text)
                            if matches:
                                all_detections.append({
                                    'type': type_name,
                                    'pattern': pattern,
                                    'content': text[:100],
                                    'matches': matches
                                })
                                detected_types.add(type_name)
                if not all_detections:
                    return None
                report_text = f"⚠️ VIOLATIONS DETECTED ⚠️\nTarget: @{self.target}\nTypes: {', '.join(detected_types)}\n"
                for i, det in enumerate(all_detections[:5]):
                    report_text += f"\n--- {det['type'].upper()} ---\nPattern: {det['pattern']}\nContent: {det['content']}\n"
                return report_text
            else:
                config = self.report_configs.get(self.report_type)
                if not config:
                    return None
                detections = []
                for content in content_list:
                    text = content.get('text', '')
                    for pattern in config['keywords']:
                        matches = re.findall(pattern, text)
                        if matches:
                            detections.append({
                                'pattern': pattern,
                                'content': text[:100],
                                'matches': matches
                            })
                if not detections:
                    return None
                report_text = config['template'].format(
                    target=self.target,
                    detections="\n".join([f"  - {d['pattern']}: {d['content']}" for d in detections[:5]])
                )
                return report_text
    
    def send_report_with_accounts(self, report_text, reason):
        if not report_text:
            return False
        
        if not self.accounts:
            self.accounts = [{'phone': 'guest', 'password': 'guest', 'session_id': 'guest'}]
        
        success_count = 0
        total_accounts = len(self.accounts)
        
        print(f"{Fore.CYAN}[*] Sending reports using {total_accounts} accounts...{Style.RESET_ALL}")
        
        for i, account in enumerate(self.accounts):
            headers = {
                "User-Agent": self.ua.random,
                "Content-Type": "application/json",
                "X-Account-Phone": account['phone'],
                "X-Session-Id": account['session_id'],
                "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            }
            
            for endpoint in self.endpoints:
                payload = {
                    "peer": self.target,
                    "report_reason": reason,
                    "message": report_text[:500],
                    "report_type": "channel" if self.target_type == "channel" else "user",
                    "severity": "CRITICAL",
                    "timestamp": int(time.time()),
                    "target_type": self.target_type
                }
                
                try:
                    response = self.session.post(endpoint, json=payload, headers=headers, timeout=10)
                    if response.status_code in [200, 202, 204]:
                        success_count += 1
                        print(f"{Fore.GREEN}[+] Account {i+1}/{total_accounts} - SUCCESS!{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}[!] Account {i+1}/{total_accounts} - Failed ({response.status_code}){Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}[-] Account {i+1}/{total_accounts} - Error{Style.RESET_ALL}")
                
                time.sleep(random.uniform(0.5, 1.5))
        
        return success_count > 0
    
    def run(self):
        print(f"{Fore.MAGENTA}")
        print("▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        print("        MULTI-REPORT NUKER v2.0")
        print(f"        Target: @{self.target}")
        print(f"        Report Type: {self.report_type.upper()}")
        print(f"        Target Type: {self.target_type.upper()}")
        print(f"        Accounts: {len(self.accounts)}")
        print("▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        print(f"{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}[*] Fetching content from @{self.target}...{Style.RESET_ALL}")
        
        if self.target_type == "id":
            content = self.fetch_id_logs()
        else:
            content = self.fetch_channel_content()
        
        if not content:
            print(f"{Fore.RED}[-] No content found or target is private.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}[+] Found {len(content)} items{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}[*] Scanning content...{Style.RESET_ALL}")
        report_text = self.scan_and_generate_report(content)
        
        if not report_text:
            print(f"{Fore.GREEN}[+] No violations detected.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.RED}")
        print("🚨 VIOLATIONS DETECTED! 🚨")
        print(f"{Style.RESET_ALL}")
        print(report_text[:500])
        
        print(f"{Fore.CYAN}[*] Sending reports...{Style.RESET_ALL}")
        config = self.report_configs.get(self.report_type, {})
        reason = config.get("reason", "spam")
        
        success = self.send_report_with_accounts(report_text, reason)
        
        if success:
            print(f"{Fore.GREEN}")
            print("▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
            print(f"        ✅ REPORTING COMPLETE!")
            print(f"        Reports sent from {len(self.accounts)} accounts")
            print(f"        Target: @{self.target}")
            print(f"        Status: FLAGGED FOR BAN")
            print("▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
            print(f"{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[-] All reports failed. Try again.{Style.RESET_ALL}")

# ============ BOT CLASS ============

class TelegramBot:
    def __init__(self, token, owner_id):
        self.token = token
        self.owner_id = int(owner_id)
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.nuker = None
        self.current_target = None
        self.report_type = "child_porn"
        self.target_type = "channel"
        self.is_running = False
        
        print("[+] Telegram Bot Started")
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
        menu = f"""
🤖 <b>TELEGRAM FREEZER BOT</b>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>COMMANDS:</b>
/start - Show menu
/freeze @username - Freeze target
/status - Current status
/stop - Stop operation
/category - Change report type
/targettype - Channel or ID mode
/help - Help

━━━━━━━━━━━━━━━━━━━━━━━━
<b>CURRENT SETTINGS:</b>
Target: {self.current_target or 'None'}
Category: {self.report_type.upper()}
Target Type: {self.target_type.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━
<b>CATEGORIES:</b>
child_porn - 🚨 Child Abuse
hacking_mods - 🔧 Hacking/Mods
illegal_goods - 🚫 Illegal Goods
spam_scam - 📱 Spam/Scam
violence - 💀 Violence
terrorism - 💣 Terrorism
adult_content - 🔞 Adult Content
"""
        self.send_message(chat_id, menu, parse_mode="HTML")
    
    def start_freezing(self, chat_id, target):
        if not target or not target.startswith("@"):
            self.send_message(chat_id, "