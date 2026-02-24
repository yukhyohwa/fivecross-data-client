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
    def __init__(self):
        self.base_url = settings.TA_URL
        self.sql_url = settings.TA_SQL_URL
        self.username = settings.TA_USER
        self.password = settings.TA_PASS
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
        """Standard login logic with ported selectors."""
        user_input = page.wait_for_selector('input[placeholder*="Account"], input[placeholder*="Username"], input[id="username"], input[type="text"]', timeout=15000)
        pass_input = page.wait_for_selector('input[placeholder*="Password"], input[id="password"], input[type="password"]', timeout=15000)
        
        user_input.fill("")
        user_input.type(self.username, delay=50)
        pass_input.fill("")
        pass_input.type(self.password, delay=50)
        
        remember_me = page.query_selector('label:has-text("7 day"), label:has-text("7天"), .ant-checkbox-wrapper, input[type="checkbox"]')
        if remember_me:
            remember_me.click()
        
        login_btn = page.wait_for_selector('button:has-text("Login"), button:has-text("登录"), button[type="submit"], .ant-btn-primary', timeout=15000)
        login_btn.click()
        
        page.wait_for_url(lambda url: "login" not in url.lower(), timeout=20000)
