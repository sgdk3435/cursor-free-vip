import os
from colorama import Fore, Style, init
import time
import random
from faker import Faker
from cursor_auth import CursorAuth
from reset_machine_manual import MachineIDResetter
from get_user_token import get_token_from_cookie
from config import get_config
from account_manager import AccountManager

os.environ["PYTHONVERBOSE"] = "0"
os.environ["PYINSTALLER_VERBOSE"] = "0"

# Initialize colorama
init()

# Define emoji constants
EMOJI = {
    'START': '🚀',
    'FORM': '📝',
    'VERIFY': '🔄',
    'PASSWORD': '🔑',
    'CODE': '📱',
    'DONE': '✨',
    'ERROR': '❌',
    'WAIT': '⏳',
    'SUCCESS': '✅',
    'MAIL': '📧',
    'KEY': '🔐',
    'UPDATE': '🔄',
    'INFO': 'ℹ️'
}

class CursorRegistration:
    def __init__(self, translator=None):
        self.translator = translator
        # Set to display mode
        os.environ['BROWSER_HEADLESS'] = 'False'
        self.browser = None
        self.controller = None
        self.sign_up_url = "https://authenticator.cursor.sh/sign-up"
        self.settings_url = "https://www.cursor.com/settings"
        self.email_address = None
        self.signup_tab = None
        self.email_tab = None
        
        # initialize Faker instance
        self.faker = Faker()
          # generate account information
        self.password = self._generate_password()
        self.first_name = self.faker.first_name()
        self.last_name = self.faker.last_name()
          # modify the first letter of the first name(keep the original function)
        new_first_letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.first_name = new_first_letter + self.first_name[1:]
        
        print(f"\n{Fore.CYAN}{EMOJI['PASSWORD']} {self.translator.get('register.password')}: {self.password} {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['FORM']} {self.translator.get('register.first_name')}: {self.first_name} {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['FORM']} {self.translator.get('register.last_name')}: {self.last_name} {Style.RESET_ALL}")
        
    def _generate_password(self, length=12):
        """Generate password"""
        return self.faker.password(length=length, special_chars=True, digits=True, upper_case=True, lower_case=True)
        
    def _get_email_config_file(self):
        """Get email configuration file path"""
        try:
            # Try to get Documents path safely
            if hasattr(self, '_get_user_documents_path'):
                documents_path = self._get_user_documents_path()
            else:
                # Fallback method
                import platform
                if platform.system() == "Windows":
                    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
                else:
                    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
            
            config_dir = os.path.join(documents_path, ".cursor-free-vip")
            if not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir, exist_ok=True)
                except Exception:
                    # 如果无法创建目录，使用当前目录
                    return os.path.join(os.getcwd(), "email_config.txt")
            
            # 尝试写入测试文件以确保有写权限
            test_path = os.path.join(config_dir, "test_write.tmp")
            try:
                with open(test_path, 'w') as f:
                    f.write("test")
                os.remove(test_path)
                return os.path.join(config_dir, "email_config.txt")
            except Exception:
                # 如果没有写权限，使用当前目录
                return os.path.join(os.getcwd(), "email_config.txt")
        except Exception:
            # Final fallback to current directory
            return os.path.join(os.getcwd(), "email_config.txt")

    def _read_email_config(self):
        """Read email configuration (template and counter)"""
        config_file = self._get_email_config_file()
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.read().strip().split('\n')
                    if len(lines) >= 2:
                        template = lines[0]
                        counter = int(lines[1])
                        return template, counter
            return None, 0
        except Exception:
            return None, 0

    def _write_email_config(self, template, counter, current_email=None):
        """Write email configuration (template, counter and current email)"""
        config_file = self._get_email_config_file()
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(f"{template}\n{counter}")
                if current_email:
                    f.write(f"\n{current_email}")
            return True
        except Exception:
            return False

    def _save_registration_record(self, email, username, password):
        """Save registration record to the top of email_config.txt"""
        config_file = self._get_email_config_file()
        try:
            # Read existing content first
            existing_content = ""
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
              # Create new record
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_record = f"[注册记录 - {timestamp}]\n"
            new_record += f"邮箱: {email}\n"
            new_record += f"用户名: {username}\n"
            new_record += f"密码: {password}\n"
            new_record += f"{'='*50}\n\n"
            
            # Write new record at the top, followed by existing content
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_record + existing_content)
            
            # 显示文件的确切位置，以便用户能找到它
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('register.registration_record_saved') if self.translator else '注册信息已保存到 email_config.txt'}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{EMOJI['INFO']} 文件位置: {os.path.abspath(config_file)}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.save_record_failed') if self.translator else '保存注册记录失败'}: {str(e)}{Style.RESET_ALL}")
            return False

    def _generate_auto_email(self):
        """Generate automatic email with counter based on template"""
        template, counter = self._read_email_config()
        
        if template is None:
            # First time - ask user for template
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('register.first_time_email_setup') if self.translator else 'First time email setup - please enter your email template:'}")
            print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('register.email_template_example') if self.translator else 'Example: aicraft000@2925.com (numbers will be added automatically)'}")
            template = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
            
            if '@' not in template:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.invalid_email_template') if self.translator else 'Invalid email template'}{Style.RESET_ALL}")
                return None, None
            
            # Save initial template with counter 0
            self._write_email_config(template, 0)
            counter = 0
          # Generate email based on template and counter
        if counter == 0:
            # First email uses template as is
            email = template
        else:
            # Add counter to the local part of email
            local_part, domain = template.split('@', 1)
            email = f"{local_part}{counter:05X}@{domain}"  # 5-digit hex format
        
        # Increment counter for next use
        self._write_email_config(template, counter + 1)
        
        return email, counter

    def setup_email(self):
        """Setup Email"""
        try:
            print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.email_options') if self.translator else 'Email Options:'}")
            print(f"{Fore.CYAN}1. {self.translator.get('register.use_auto_email') if self.translator else '使用无限邮（仅首次输入邮箱）'}")
            print(f"{Fore.CYAN}2. {self.translator.get('register.use_suggested_email') if self.translator else 'Use suggested email'}")
            print(f"{Fore.CYAN}3. {self.translator.get('register.manual_email_input') if self.translator else 'Enter custom email'}")
            
            choice = input(f"{self.translator.get('register.choose_option') if self.translator else 'Choose option (1-3): '}").strip()
            
            if choice == '1':
                # Use automatic email with counter
                result = self._generate_auto_email()
                if result is None or result[0] is None:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.email_template_failed') if self.translator else 'Failed to setup email template'}{Style.RESET_ALL}")
                    return False
                
                auto_email, counter = result
                self.email_address = auto_email
                print(f"{Fore.GREEN}{EMOJI['MAIL']} {self.translator.get('register.auto_email_generated') if self.translator else 'Auto email generated'}: {auto_email}")
                print(f"{Fore.YELLOW}{EMOJI['INFO']} {self.translator.get('register.current_counter') if self.translator else 'Current counter'}: {counter} (0x{format(counter, '05X')})")
                
            elif choice == '2':
                # Use suggested email (original logic)
                account_manager = AccountManager(self.translator)
                suggested_email = account_manager.suggest_email(self.first_name, self.last_name)
                
                if suggested_email:
                    print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.suggest_email', suggested_email=suggested_email) if self.translator else f'Suggested email: {suggested_email}'}")
                    print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.use_suggested_email_or_enter') if self.translator else 'Type \"yes\" to use this email or enter your own email:'}")
                    user_input = input().strip()
                    
                    if user_input.lower() == 'yes' or user_input.lower() == 'y':
                        self.email_address = suggested_email
                    else:
                        # User input is their own email address
                        self.email_address = user_input
                else:
                    # If there's no suggested email, fall back to manual input
                    print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.manual_email_input') if self.translator else 'Please enter your email address:'}")
                    self.email_address = input().strip()
                    
            elif choice == '3':
                # Manual email input
                print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.manual_email_input') if self.translator else 'Please enter your email address:'}")
                self.email_address = input().strip()
                
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.invalid_choice') if self.translator else 'Invalid choice, using unlimited email'}")
                result = self._generate_auto_email()
                if result is None or result[0] is None:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.email_template_failed') if self.translator else 'Failed to setup email template'}{Style.RESET_ALL}")
                    return False
                
                auto_email, counter = result
                self.email_address = auto_email
                print(f"{Fore.GREEN}{EMOJI['MAIL']} {self.translator.get('register.auto_email_generated') if self.translator else 'Auto email generated'}: {auto_email}")
            
            # Validate if the email is valid
            if '@' not in self.email_address:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.invalid_email') if self.translator else 'Invalid email address'}{Style.RESET_ALL}")
                return False
                
            print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('register.email_address')}: {self.email_address}" + "\n" + f"{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.email_setup_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def get_verification_code(self):
        """Manually Get Verification Code"""
        try:
            print(f"{Fore.CYAN}{EMOJI['CODE']} {self.translator.get('register.manual_code_input') if self.translator else 'Please enter the verification code:'}")
            code = input().strip()
            
            if not code.isdigit() or len(code) != 6:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.invalid_code') if self.translator else 'Invalid verification code'}{Style.RESET_ALL}")
                return None
                
            return code
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.code_input_failed', error=str(e))}{Style.RESET_ALL}")
            return None

    def register_cursor(self):
        """Register Cursor"""
        browser_tab = None
        try:
            print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.register_start')}...{Style.RESET_ALL}")
            
            # Check if tempmail_plus is enabled
            config = get_config(self.translator)
            email_tab = None
            if config and config.has_section('TempMailPlus'):
                if config.getboolean('TempMailPlus', 'enabled'):
                    email = config.get('TempMailPlus', 'email')
                    epin = config.get('TempMailPlus', 'epin')
                    if email and epin:
                        from email_tabs.tempmail_plus_tab import TempMailPlusTab
                        email_tab = TempMailPlusTab(email, epin, self.translator)
                        print(f"{Fore.CYAN}{EMOJI['MAIL']} {self.translator.get('register.using_tempmail_plus')}{Style.RESET_ALL}")
            
            # Use new_signup.py directly for registration
            from new_signup import main as new_signup_main
            
            # Execute new registration process, passing translator
            result, browser_tab = new_signup_main(
                email=self.email_address,
                password=self.password,
                first_name=self.first_name,
                last_name=self.last_name,
                email_tab=email_tab,  # Pass email_tab if tempmail_plus is enabled
                controller=self,  # Pass self instead of self.controller
                translator=self.translator
            )
            
            if result:
                # Use the returned browser instance to get account information
                self.signup_tab = browser_tab  # Save browser instance
                success = self._get_account_info()
                
                # Close browser after getting information
                if browser_tab:
                    try:
                        browser_tab.quit()
                    except:
                        pass
                
                return success
            
            return False
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.register_process_error', error=str(e))}{Style.RESET_ALL}")
            return False
        finally:
            # Ensure browser is closed in any case
            if browser_tab:
                try:
                    browser_tab.quit()
                except:
                    pass
                
    def _get_account_info(self):
        """Get Account Information and Token"""
        try:
            self.signup_tab.get(self.settings_url)
            time.sleep(2)
            
            usage_selector = (
                "css:div.col-span-2 > div > div > div > div > "
                "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
                "span.font-mono.text-sm\\/\\[0\\.875rem\\]"
            )
            usage_ele = self.signup_tab.ele(usage_selector)
            total_usage = "未知"
            if usage_ele:
                total_usage = usage_ele.text.split("/")[-1].strip()

            print(f"Total Usage: {total_usage}\n")
            print(f"{Fore.CYAN}{EMOJI['WAIT']} {self.translator.get('register.get_token')}...{Style.RESET_ALL}")
            max_attempts = 30
            retry_interval = 2
            attempts = 0

            while attempts < max_attempts:                
                try:
                    cookies = self.signup_tab.cookies()
                    for cookie in cookies:
                        if cookie.get("name") == "WorkosCursorSessionToken":
                            token = get_token_from_cookie(cookie["value"], self.translator)
                            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('register.token_success')}{Style.RESET_ALL}")
                            self._save_account_info(token, total_usage)
                            return True

                    attempts += 1
                    if attempts < max_attempts:
                        print(f"{Fore.YELLOW}{EMOJI['WAIT']} {self.translator.get('register.token_attempt', attempt=attempts, time=retry_interval)}{Style.RESET_ALL}")
                        time.sleep(retry_interval)
                    else:
                        print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.token_max_attempts', max=max_attempts)}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.token_failed', error=str(e))}{Style.RESET_ALL}")
                    attempts += 1
                    if attempts < max_attempts:
                        print(f"{Fore.YELLOW}{EMOJI['WAIT']} {self.translator.get('register.token_attempt', attempt=attempts, time=retry_interval)}{Style.RESET_ALL}")
                        time.sleep(retry_interval)

            return False

        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.account_error', error=str(e))}{Style.RESET_ALL}")
            return False

    def _save_account_info(self, token, total_usage):
        """Save Account Information to File"""
        try:
            # Update authentication information first
            print(f"{Fore.CYAN}{EMOJI['KEY']} {self.translator.get('register.update_cursor_auth_info')}...{Style.RESET_ALL}")
            if self.update_cursor_auth(email=self.email_address, access_token=token, refresh_token=token, auth_type="Auth_0"):
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('register.cursor_auth_info_updated')}...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.cursor_auth_info_update_failed')}...{Style.RESET_ALL}")

            # Reset machine ID
            print(f"{Fore.CYAN}{EMOJI['UPDATE']} {self.translator.get('register.reset_machine_id')}...{Style.RESET_ALL}")
            resetter = MachineIDResetter(self.translator)  # Create instance with translator
            if not resetter.reset_machine_ids():  # Call reset_machine_ids method directly
                raise Exception("Failed to reset machine ID")
            
            # Save account information to file using AccountManager
            account_manager = AccountManager(self.translator)
            if account_manager.save_account_info(self.email_address, self.password, token, total_usage):
                # Save registration record to email_config.txt
                full_name = f"{self.first_name} {self.last_name}"
                self._save_registration_record(self.email_address, full_name, self.password)
                return True
            else:
                return False
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.save_account_info_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def start(self):
        """Start Registration Process"""
        try:
            if self.setup_email():
                if self.register_cursor():
                    print(f"\n{Fore.GREEN}{EMOJI['DONE']} {self.translator.get('register.cursor_registration_completed')}...{Style.RESET_ALL}")
                    return True
            return False
        finally:
            # Close email tab
            if hasattr(self, 'temp_email'):
                try:
                    self.temp_email.close()
                except:
                    pass

    def update_cursor_auth(self, email=None, access_token=None, refresh_token=None, auth_type="Auth_0"):
        """Convenient function to update Cursor authentication information"""
        auth_manager = CursorAuth(translator=self.translator)
        return auth_manager.update_auth(email, access_token, refresh_token, auth_type)

def main(translator=None):
    """Main function to be called from main.py"""
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['START']} {translator.get('register.title')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    registration = CursorRegistration(translator)
    registration.start()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {translator.get('register.press_enter')}...")

if __name__ == "__main__":
    from main import translator as main_translator
    main(main_translator) 