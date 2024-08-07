import os

if os.getenv('ENV') == 'LOCAL':
    from dotenv import load_dotenv

    load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, 'shopen/assets')

DB_CONFIG = {
    "connections": {
        "default": "sqlite://db.sqlite3",
    },
    "apps": {
        "models": {
            "models": ["shopen.models.models"],
            "default_connection": "default",
        },
    },
}

SUPER_ADMIN_TOKEN = os.getenv('SUPER_ADMIN_TOKEN', default='123456')
ADMIN_DISCOUNT = float(os.getenv('ADMIN_DISCOUNT', default=0.2))
WHOLESALE_DISCOUNT = float(os.getenv('WHOLESALE_DISCOUNT', default=0.1))
WHOLESALE_THRESHOLD = int(os.getenv('WHOLESALE_THRESHOLD', default=5_000))
TRANSACTION_REQUEST_THRESHOLD = int(os.getenv('TRANSACTION_REQUEST_MINUTES', default=5))
TRANSACTION_REFUND_THRESHOLD = int(os.getenv('TRANSACTION_REFUND_MINUTES', default=20))
