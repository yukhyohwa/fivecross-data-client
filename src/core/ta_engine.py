import os
import time
from playwright.sync_api import sync_playwright
from src.core.base_engine import BaseEngine
from src.utils.logger import logger
from src.config import settings

class ThinkingDataEngine(BaseEngine):
    """
    Engine for ThinkingData platform using Playwright automation.
    Logic fully synchronized with thinking-data-client/src/connector.py
    """
    def __init__(self, config):
        self.config = config
        self.base_url = config.url
        self.sql_url = config.sql_url
        self.username = config.user
        self.password = config.password
        self.user_data_dir = settings.TA_SESSION_DIR

    def login(self, headless=False):
        """
        Executes login flow. Strictly following old project's logic.
        """
        if not self.username or not self.password:
            logger.error("TA credentials missing.")
            return

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                slow_mo=100,
                permissions=["clipboard-read", "clipboard-write"]
            )
            page = context.new_page()
            logger.info(f"Navigating to login page: {self.base_url}")
            page.goto(self.base_url)
            
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

            is_login_page = "login" in page.url.lower() or \
                           page.query_selector('input[type="password"]') or \
                           page.query_selector('input[placeholder*="Password"]')

            if is_login_page:
                logger.info("Login page detected, performing auto-login...")
                try:
                    self._perform_login_logic(page)
                    logger.info("Auto-login successful!")
                except Exception as e:
                    logger.error(f"Auto-login failed: {e}")
                    if not os.path.exists("output"): os.makedirs("output")
                    page.screenshot(path="output/login_failed.png")
            else:
                logger.info("Active session detected, skipping login.")
            
            time.sleep(2)
            context.close()

    def fetch(self, sql: str, **kwargs) -> list:
        return self.run_sql_query(sql_text=sql, headless=kwargs.get('headless', True))

    def run_sql_query(self, sql_text=None, headless=True):
        """
        Full query logic including the requested 'Feedback' (status logging).
        Ported from thinking-data-client/src/connector.py
        """
        results_data = []

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                slow_mo=100, # Increased slow_mo for stability
                permissions=["clipboard-read", "clipboard-write"]
            )
            page = context.new_page()

            def handle_response(response):
                try:
                    if response.status == 200 and "json" in response.headers.get("content-type", "").lower():
                        data = response.json()
                        payload = data.get("data", data) if isinstance(data, dict) else data
                        if isinstance(payload, dict):
                            for key in ["rows", "result", "results", "list"]:
                                if key in payload and isinstance(payload[key], list) and len(payload[key]) > 0:
                                    if any(k in payload for k in ["header", "columns", "headers"]):
                                        results_data.append(payload)
                                        logger.info(f"Intercepted data via key [{key}]: {len(payload[key])} rows.")
                                        return
                except:
                    pass

            page.on("response", handle_response)
            
            logger.info(f"Opening IDE page: {self.sql_url}")
            page.goto(self.sql_url)
            
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
                
                # Auto-login if session expired
                if "login" in page.url.lower() or page.query_selector('input[type="password"]'):
                    logger.info("Session expired. Performing auto-login...")
                    self._perform_login_logic(page)
                    page.goto(self.sql_url)
                    page.wait_for_load_state("networkidle", timeout=15000)

                if sql_text:
                    logger.info("Injecting SQL into editor...")
                    editor_selector = ".monaco-editor, .CodeMirror, .ace_editor, textarea"
                    editor = page.wait_for_selector(editor_selector, timeout=20000)
                    editor.click()
                    
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.wait_for_timeout(500)
                    
                    # Direct Monaco injection
                    try:
                        success = page.evaluate("""(text) => {
                            if (window.monaco && monaco.editor.getModels().length > 0) {
                                monaco.editor.getModels()[0].setValue(text);
                                return true;
                            }
                            const models = window.monaco?.editor?.getModels();
                            if (models && models.length > 0) {
                                models[0].setValue(text);
                                return true;
                            }
                            return false;
                        }""", sql_text)
                    except:
                        success = False

                    if not success:
                        logger.info("Using keyboard.insert_text fallback...")
                        editor.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.keyboard.insert_text(sql_text)
                    
                    page.wait_for_timeout(2000)

                    # Trigger Calculate
                    calc_btn = page.query_selector('button:has-text("Calculate"), button:has-text("计算"), .ant-btn:has-text("计算")')
                    if calc_btn:
                        logger.info("Triggering 'Calculate' button...")
                        calc_btn.click()
                    else:
                        logger.info("Triggering Ctrl+Enter...")
                        page.keyboard.press("Control+Enter")

                # Feedback mechanism
                logger.info("Waiting for data (checking engine status)...")
                max_timeout = 3600 
                start_time = time.time()
                
                while not results_data and (time.time() - start_time < max_timeout):
                    # 1. Download check
                    download_btn = page.query_selector('button:has-text("Download All"), button:has-text("全量下载"), .ant-btn:has-text("全量下载")')
                    if download_btn:
                        logger.info("Success! Downloading output...")
                        with page.expect_download(timeout=60000) as download_info:
                            download_btn.click()
                        download = download_info.value
                        if not os.path.exists("output"): os.makedirs("output")
                        download_path = os.path.join("output", download.suggested_filename)
                        download.save_as(download_path)
                        results_data.append({"file_path": download_path, "type": "file"})
                        break

                    # 2. Progress Feedback
                    status_area = page.query_selector('.ant-tabs-tabpane-active, .ide-results-area')
                    status_text = status_area.inner_text() if status_area else ""
                    
                    is_running = "查询引擎运行中" in status_text or \
                                 "已进行" in status_text or \
                                 page.query_selector('.ant-spin-spinning, .ant-progress-circle')
                    
                    if is_running:
                        elapsed = int(time.time() - start_time)
                        if elapsed % 15 == 0:
                            logger.info(f"Feedback: Progressing... [{status_text.strip() if status_text else 'Calculating'}]")
                        page.wait_for_timeout(3000)
                        continue

                    # 3. Error detection
                    error_indicators = ["java.sql.SQLException", "Parse exception", "Error", "mismatched input", "cannot be resolved"]
                    if any(ind in status_text for ind in error_indicators):
                        logger.error(f"SQL failed: {status_text.strip()}")
                        break

                    page.wait_for_timeout(3000)
                    
                    # 4. Idle check
                    calc_ready = page.query_selector('button:has-text("Calculate"), button:has-text("计算")')
                    if calc_ready and calc_ready.is_enabled() and not results_data:
                        logger.info("IDE idle. No data captured.")
                        break

                if not results_data:
                    if not os.path.exists("output"): os.makedirs("output")
                    page.screenshot(path="output/final_error_debug.png")

            except Exception as e:
                logger.error(f"Execution failed: {e}")
                if not os.path.exists("output"): os.makedirs("output")
                page.screenshot(path="output/exception_error_debug.png")
            
            context.close()
        return results_data

    def _perform_login_logic(self, page):
        """Standard login logic with ported selectors, enhanced for China region."""
        # 1. Find Inputs
        user_input = page.wait_for_selector('input[placeholder*="Account"], input[placeholder*="Username"], input[placeholder*="账号"], input[id="username"], input[type="text"]', timeout=15000)
        pass_input = page.wait_for_selector('input[placeholder*="Password"], input[placeholder*="密码"], input[id="password"], input[type="password"]', timeout=15000)
        
        # 2. Fill Credentials
        user_input.fill("")
        user_input.type(self.username, delay=30)
        pass_input.fill("")
        pass_input.type(self.password, delay=30)
        
        # 3. Handle Remember Me (Optional)
        try:
            remember_me = page.query_selector('label:has-text("7 day"), label:has-text("7天"), .ant-checkbox-wrapper, input[type="checkbox"]')
            if remember_me:
                # Check if it's already checked to avoid unchecking
                is_checked = page.evaluate("(el) => el.classList.contains('ant-checkbox-wrapper-checked') || (el.querySelector('input') && el.querySelector('input').checked)", remember_me)
                if not is_checked:
                    remember_me.click()
        except:
            pass
        
        # 4. Click Login or Press Enter
        page.wait_for_timeout(1000)
        
        button_clicked = False
        try:
            # Try Playwright's most robust locators first
            login_btn = page.get_by_role("button", name="登录").or_(page.get_by_text("登录", exact=True)).first
            if login_btn.is_visible():
                logger.info("Clicking '登录' button via robust locator...")
                login_btn.click()
                button_clicked = True
        except:
            pass

        if not button_clicked:
            # Fallback to secondary selectors
            login_btn_selectors = [
                'button:has-text("登录")',
                '.ant-btn-primary',
                'button[type="submit"]',
                'div.ant-btn-primary'
            ]
            for selector in login_btn_selectors:
                try:
                    candidate = page.query_selector(selector)
                    if candidate and candidate.is_visible():
                        logger.info(f"Attempting to click login button: {selector}")
                        candidate.click()
                        button_clicked = True
                        break
                except: continue

        # Ensure focus is on password field before pressing Enter as a final fallback
        page.wait_for_timeout(1000)
        logger.info("Performing final submission check (Enter key fallback)...")
        pass_input.focus()
        page.keyboard.press("Enter")
            
        # 5. Wait for outcome (Resilient strategy)
        try:
            # Fix: CSS selector :has-text() is a Playwright extension and doesn't work in native document.querySelector
            page.wait_for_function("""() => {
                const buttons = Array.from(document.querySelectorAll('button, .ant-btn'));
                const hasLoginButton = buttons.some(btn => btn.innerText.includes('登录') || btn.innerText.includes('Login'));
                return !hasLoginButton || !window.location.href.toLowerCase().includes('login');
            }""", timeout=20000)
            logger.info("Login form submitted successfully.")
        except Exception as e:
            logger.warn(f"Wait for login transition timed out, but proceeding anyway.")
            
        # Final safety sleep for redirection
        page.wait_for_timeout(3000)
