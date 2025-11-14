import os
basedir = os.path.abspath(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

class Config:
    # --------------------------
    # Flask Config
    # --------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    
    # --------------------------
    # MySQL Database Config
    # --------------------------
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'villain_food_app')
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', os.path.join(basedir, 'data', 'villain_food.db'))
    
    # --------------------------
    # SQLAlchemy (optional, if you switch to ORM)
    # --------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --------------------------
    # Uploads
    # --------------------------
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'images')
    
    # --------------------------
    # AI & Blockchain Paths (optional)
    # --------------------------
    AI_MODEL_PATH = os.environ.get('AI_MODEL_PATH', os.path.join(basedir, 'ai', 'model.pkl'))
    BLOCKCHAIN_LEDGER_PATH = os.environ.get('BLOCKCHAIN_LEDGER_PATH', os.path.join(basedir, 'blockchain', 'ledger.json'))
    AI_DATASET_PATH = os.environ.get('AI_DATASET_PATH', os.path.join(basedir, 'docs', 'ai', 'villain_sales_dataset.csv'))
    SECURITY_DOMAIN = os.environ.get('SECURITY_DOMAIN', 'https://security.villain-food-app.com')
    DATA_CLASSIFICATION_PATH = os.environ.get('DATA_CLASSIFICATION_PATH', os.path.join(basedir, 'docs', 'cybersecurity', 'data_classification.csv'))
    GDPR_COMPLIANCE_PATH = os.environ.get('GDPR_COMPLIANCE_PATH', os.path.join(basedir, 'docs', 'cybersecurity', 'gdpr_compliance.csv'))
    
    # --------------------------
    # Ethereum / Blockchain Config
    # --------------------------
    ETHEREUM_RPC_URL = os.environ.get('ETHEREUM_RPC_URL', 'http://localhost:8545')
    ETHEREUM_PRIVATE_KEY = os.environ.get('ETHEREUM_PRIVATE_KEY', '')
    ORDER_CONTRACT_ADDRESS = os.environ.get('ORDER_CONTRACT_ADDRESS', '')
    TOKEN_CONTRACT_ADDRESS = os.environ.get('TOKEN_CONTRACT_ADDRESS', '')
    USE_ETHEREUM = os.environ.get('USE_ETHEREUM', 'false').lower() == 'true'
    
    # --------------------------
    # App Environment
    # --------------------------
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('DEBUG', True)
