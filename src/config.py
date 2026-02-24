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

class Settings:
    # --- AliCloud Credentials ---
    ALI_CREDENTIALS = {
        'china': {
            'odps': DBConfig(
                access_id=os.getenv('ALIYUN_AK_CN', ''),
                access_key=os.getenv('ALIYUN_SK_CN', ''),
                endpoint='http://service.odps.aliyun.com/api',
                project='g13001230'
            ),
            'holo': DBConfig(
                access_id=os.getenv('ALIYUN_AK_CN', ''),
                access_key=os.getenv('ALIYUN_SK_CN', ''),
                host='hgprecn-cn-n6w1y5llh002-cn-hangzhou.hologres.aliyuncs.com',
                port=80,
                dbname='online',
                user=os.getenv('ALIYUN_AK_CN', ''),
                password=os.getenv('ALIYUN_SK_CN', '')
            )
        },
        'global': {
            'odps': DBConfig(
                access_id=os.getenv('ALIYUN_AK_OVERSEAS', ''),
                access_key=os.getenv('ALIYUN_SK_OVERSEAS', ''),
                endpoint='http://service.ap-northeast-1.maxcompute.aliyun.com/api',
                project='g65002007'
            ),
            'holo': DBConfig(
                access_id=os.getenv('ALIYUN_AK_OVERSEAS', ''),
                access_key=os.getenv('ALIYUN_SK_OVERSEAS', ''),
                host='hgpre-sg-6wr2ald3b002-ap-northeast-1.hologres.aliyuncs.com',
                port=80,
                dbname='online',
                user=os.getenv('ALIYUN_AK_OVERSEAS', ''),
                password=os.getenv('ALIYUN_SK_OVERSEAS', '')
            )
        }
    }

    # --- ThinkingData Credentials ---
    TA_URL = os.getenv("TA_URL", "http://8.211.141.76:8993/")
    TA_USER = os.getenv("TA_USER", "")
    TA_PASS = os.getenv("TA_PASS", "")
    TA_SQL_URL = os.getenv("TA_SQL_URL", f"{TA_URL}#/tga/ide/-1")
    TA_SESSION_DIR = os.path.abspath(os.getenv("USER_DATA_DIR", "./ta_session"))

    # --- Email Config ---
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', '')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')

settings = Settings()
