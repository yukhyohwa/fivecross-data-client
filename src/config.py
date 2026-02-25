import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class DBConfig:
    access_id: str = ""
    access_key: str = ""
    endpoint: str = ""
    project: str = ""
    host: str = ""
    port: int = 80
    dbname: str = ""
    user: str = ""
    password: str = ""

@dataclass
class TAConfig:
    url: str = ""
    sql_url: str = ""
    user: str = ""
    password: str = ""

class Settings:
    # --- AliCloud Credentials ---
    ALI_CREDENTIALS = {
        'china': {
            'odps': DBConfig(
                access_id=os.getenv('ALIYUN_AK_CN', ''),
                access_key=os.getenv('ALIYUN_SK_CN', ''),
                endpoint='http://service.odps.aliyun.com/api',
                project=os.getenv('ALIYUN_PROJECT_CN', 'your_china_project')
            ),
            'holo': DBConfig(
                access_id=os.getenv('ALIYUN_AK_CN', ''),
                access_key=os.getenv('ALIYUN_SK_CN', ''),
                host=os.getenv('HOLO_HOST_CN', 'your_china_holo_host'),
                port=int(os.getenv('HOLO_PORT_CN', '80')),
                dbname=os.getenv('HOLO_DB_CN', 'online'),
                user=os.getenv('ALI_USER_CN', os.getenv('ALIYUN_AK_CN', '')),
                password=os.getenv('ALI_PASS_CN', os.getenv('ALIYUN_SK_CN', ''))
            )
        },
        'global': {
            'odps': DBConfig(
                access_id=os.getenv('ALIYUN_AK_OVERSEAS', ''),
                access_key=os.getenv('ALIYUN_SK_OVERSEAS', ''),
                endpoint='http://service.ap-northeast-1.maxcompute.aliyun.com/api',
                project=os.getenv('ALIYUN_PROJECT_GLOBAL', 'your_global_project')
            ),
            'holo': DBConfig(
                access_id=os.getenv('ALIYUN_AK_OVERSEAS', ''),
                access_key=os.getenv('ALIYUN_SK_OVERSEAS', ''),
                host=os.getenv('HOLO_HOST_GLOBAL', 'your_global_holo_host'),
                port=int(os.getenv('HOLO_PORT_GLOBAL', '80')),
                dbname=os.getenv('HOLO_DB_GLOBAL', 'online'),
                user=os.getenv('ALI_USER_GLOBAL', os.getenv('ALIYUN_AK_OVERSEAS', '')),
                password=os.getenv('ALI_PASS_GLOBAL', os.getenv('ALIYUN_SK_OVERSEAS', ''))
            )
        }
    }

    # --- ThinkingData Credentials ---
    TA_CREDENTIALS = {
        'china': TAConfig(
            url=os.getenv("TA_URL_CN", "https://your-ta-china-url.com/"),
            sql_url=os.getenv("TA_SQL_URL_CN", "https://your-ta-china-url.com/#/tga/ide/-1"),
            user=os.getenv("TA_USER_CN", ""),
            password=os.getenv("TA_PASS_CN", "")
        ),
        'global': TAConfig(
            url=os.getenv("TA_URL_GLOBAL", "https://your-ta-global-url.com/"),
            sql_url=os.getenv("TA_SQL_URL_GLOBAL", "https://your-ta-global-url.com/#/tga/ide/-1"),
            user=os.getenv("TA_USER_GLOBAL", ""),
            password=os.getenv("TA_PASS_GLOBAL", "")
        )
    }
    
    TA_SESSION_DIR = os.path.abspath(os.getenv("USER_DATA_DIR", "./ta_session"))

    # --- Data & Task Path Config ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    INPUT_DIR = os.path.join(DATA_DIR, "input")
    OUTPUT_DIR = os.path.join(DATA_DIR, "output")
    # 统一输出路径，不再区分子目录
    EXPORT_DIR = OUTPUT_DIR 
    REPORT_DIR = OUTPUT_DIR 
    
    TASKS_DIR = os.path.join(BASE_DIR, "tasks")
    TEMPLATES_DIR = os.path.join(TASKS_DIR, "templates")
    CONFIGS_DIR = os.path.join(TASKS_DIR, "configs")
    JOBS_DIR = os.path.join(TASKS_DIR, "jobs")
    PREDICT_DIR = os.path.join(TASKS_DIR, "predict")
    PREDICT_INPUT_DIR = os.path.join(PREDICT_DIR, "input")

    # --- Email Config ---
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')

    def __post_init__(self):
        # 确保目录存在
        dirs_to_create = [
            self.INPUT_DIR, self.OUTPUT_DIR,
            self.TEMPLATES_DIR, self.CONFIGS_DIR, self.JOBS_DIR,
            self.PREDICT_INPUT_DIR, self.TA_SESSION_DIR
        ]
        for path in dirs_to_create:
            os.makedirs(path, exist_ok=True)

settings = Settings()
settings.__post_init__()
