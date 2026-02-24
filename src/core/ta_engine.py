import os
import time
from playwright.sync_api import sync_playwright
from src.core.base_engine import BaseEngine
from src.utils.logger import logger

class ThinkingDataEngine(BaseEngine):
    """
    Engine for ThinkingData platform using Playwright automation.
    """
    def __init__(self):
        self.base_url = os.getenv("TA_URL", "http://8.211.141.76:8993/")
        self.sql_url = os.getenv("TA_SQL_URL", "http://8.211.141.76:8993/#/tga/ide/-1")
        self.username = os.getenv("TA_USER")
        self.password = os.getenv("TA_PASS")
        self.user_data_dir = os.path.abspath(os.getenv("USER_DATA_DIR", "./ta_session"))

    def login(self, headless=False):
        """
        Executes login flow and saves session persistent context.
        """
        if not self.username or not self.password:
            logger.error("TA_USER or TA_PASS not set in environment.")
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
                    user_input = page.wait_for_selector('input[placeholder*="Account"], input[placeholder*="Username"], input[id="username"], input[type="text"]', timeout=10000)
                    pass_input = page.wait_for_selector('input[placeholder*="Password"], input[id="password"], input[type="password"]', timeout=10000)
                    
                    user_input.fill("")
                    user_input.type(self.username, delay=50)
                    pass_input.fill("")
                    pass_input.type(self.password, delay=50)
                    
                    remember_me = page.query_selector('label:has-text("7 day"), label:has-text("7天")')
                    if remember_me:
                        remember_me.click()
                    
                    login_btn = page.wait_for_selector('button:has-text("Login"), button:has-text("登录"), button[type="submit"]', timeout=5000)
                    login_btn.click()
                    
                    page.wait_for_url(lambda url: "login" not in url.lower(), timeout=15000)
                    logger.info("Auto-login successful!")
                except Exception as e:
                    logger.error(f"Auto-login failed: {str(e)}")
            else:
                logger.info("Active session detected, skipping login.")
            
            time.sleep(2)
            context.close()

    def fetch(self, sql: str, **kwargs) -> list:
        """
        Implementation of the fetch method for ThinkingData.
        Returns a list containing the data (file info or raw rows).
        """
        return self.run_sql_query(sql_text=sql, headless=kwargs.get('headless', True))

    def run_sql_query(self, sql_text=None, headless=True):
        results_data = []
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                slow_mo=500 if not headless else 0,
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
                                        return
                except:
                    pass

            page.on("response", handle_response)
            page.goto(self.sql_url)
            
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
                if sql_text:
                    logger.info("Injecting SQL into editor...")
                    editor = page.wait_for_selector(".monaco-editor, .CodeMirror, .ace_editor, textarea", timeout=20000)
                    editor.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.wait_for_timeout(500)
                    
                    success = page.evaluate("""(text) => {
                        if (window.monaco && monaco.editor.getModels().length > 0) {
                            monaco.editor.getModels()[0].setValue(text);
                            return true;
                        }
                        return false;
                    }""", sql_text)
                    
                    if not success:
                        page.keyboard.insert_text(sql_text)
                    
                    page.wait_for_timeout(1000)
                    calc_btn = page.query_selector('button:has-text("Calculate"), button:has-text("计算")')
                    if calc_btn:
                        calc_btn.click()
                    else:
                        page.keyboard.press("Control+Enter")

                max_timeout = 3600 
                start_time = time.time()
                while not results_data and (time.time() - start_time < max_timeout):
                    download_btn = page.query_selector('button:has-text("Download All"), button:has-text("全量下载")')
                    if download_btn:
                        with page.expect_download(timeout=60000) as download_info:
                            download_btn.click()
                        download = download_info.value
                        if not os.path.exists("output"): os.makedirs("output")
                        download_path = os.path.join("output", download.suggested_filename)
                        download.save_as(download_path)
                        results_data.append({"file_path": download_path, "type": "file"})
                        break

                    status_area = page.query_selector('.ant-tabs-tabpane-active, .ide-results-area')
                    status_text = status_area.inner_text() if status_area else ""
                    if "查询引擎运行中" in status_text or "已进行" in status_text or page.query_selector('.ant-spin-spinning, .ant-progress-circle'):
                        page.wait_for_timeout(3000)
                        continue

                    error_indicators = ["java.sql.SQLException", "Parse exception", "mismatched input", "Error", "cannot be resolved"]
                    if any(ind in status_text for ind in error_indicators):
                        logger.error(f"SQL failed: {status_text.strip()}")
                        break

                    page.wait_for_timeout(2000)
                    if page.query_selector('button:has-text("Calculate"), button:has-text("计算")') and not results_data:
                        break

                if not results_data:
                    if not os.path.exists("output"): os.makedirs("output")
                    page.screenshot(path="output/final_state_debug.png")

            except Exception as e:
                logger.error(f"Execution failed: {e}")
            
            context.close()
        return results_data
