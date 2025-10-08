from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from sqlalchemy import inspect
from contextlib import contextmanager

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(String, unique=True, nullable=False)  # LINE Bot識別子
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="company")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    line_user_id = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    username = Column(String)
    foot_check_result = Column(String(1))  # A/B/C/D
    program_sent_date = Column(DateTime)
    last_program_type = Column(String)  # "initial" or "continued"
    last_response_days = Column(Integer)
    question_sent = Column(Boolean, default=False)  # 質問送信状態を管理
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("MessageLog", back_populates="user")
    company = relationship("Company", back_populates="users")
    
    # line_user_idとcompany_idの組み合わせでユニーク制約
    __table_args__ = (UniqueConstraint('line_user_id', 'company_id', name='_line_user_company_uc'),)

class MessageLog(Base):
    __tablename__ = 'message_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message_type = Column(String)  # "received" or "sent"
    message_content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")

# PostgreSQL接続用エンジン作成関数
def get_engine(database_url):
    return create_engine(
        database_url, 
        echo=False, 
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800  # 30分でコネクションをリサイクル
    )

# Session作成
def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

# コンテキストマネージャーを使用したセッション管理
@contextmanager
def get_db_session(database_url):
    engine = get_engine(database_url)
    session = get_session(engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()

def run_migrations(database_url):
    """データベースのマイグレーションを実行する関数"""
    engine = get_engine(database_url)
    
    # テーブルが存在するか確認
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 必要なテーブルを作成
    Base.metadata.create_all(engine)
    
    # 既存のテーブルと新しいテーブルの差分を確認
    new_tables = set(Base.metadata.tables.keys())
    added_tables = new_tables - set(existing_tables)
    
    if added_tables:
        print(f"Created new tables: {added_tables}")
    
    return engine

def ensure_companies_exist():
    """設定されているbot_idに対応する企業レコードを確認・作成する"""
    from config import BOT_CONFIGS, DATABASE_URL
    
    with get_db_session(DATABASE_URL) as session:
        for bot_id, config in BOT_CONFIGS.items():
            company = session.query(Company).filter_by(bot_id=bot_id).first()
            if not company:
                # 新規企業レコード作成
                company = Company(
                    bot_id=bot_id,
                    name=config.get("name", f"企業 {bot_id}")
                )
                session.add(company)
                print(f"Created company record for {bot_id}: {config.get('name')}")
            else:
                # 既存企業の名前が変更されている場合は更新
                if company.name != config.get("name", f"企業 {bot_id}"):
                    old_name = company.name
                    company.name = config.get("name", f"企業 {bot_id}")
                    print(f"Updated company name for {bot_id}: {old_name} -> {company.name}")
        
        session.commit()
        
        # デバッグのために全企業レコードを表示
        companies = session.query(Company).all()
        print(f"確認: 現在のデータベース上の企業レコード:")
        for c in companies:
            print(f"  - ID: {c.id}, bot_id: {c.bot_id}, name: {c.name}")
