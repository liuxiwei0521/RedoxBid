import sqlite3
import pandas as pd
import json
from datetime import datetime

# 假设数据库文件在项目根目录
DB_PATH = "station_archive.db"

DEFAULT_STATION_PROFILE = {
    "station_name": "三峡能源新疆吉木萨尔全钒液流储能电站",
    "location": "新疆维吾尔自治区昌吉回族自治州吉木萨尔县",
    "commission_date": "2025-12-31",
    "e_rated": 1000.0,
    "p_rated": 200.0,
}

def get_db_connection():
    """建立并返回数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库，创建必要的表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建电站档案表 (只存储一条记录)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS station_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    station_name TEXT NOT NULL DEFAULT '未命名电站',
    location TEXT DEFAULT '未知地点',
    commission_date TEXT,
    e_rated REAL DEFAULT 100.0,
    p_rated REAL DEFAULT 25.0
    )
    ''')

    cursor.execute('''
    INSERT OR IGNORE INTO station_profile (id, station_name, location, commission_date, e_rated, p_rated)
    VALUES (1, ?, ?, ?, ?, ?)
    ''', (
        DEFAULT_STATION_PROFILE["station_name"],
        DEFAULT_STATION_PROFILE["location"],
        DEFAULT_STATION_PROFILE["commission_date"],
        DEFAULT_STATION_PROFILE["e_rated"],
        DEFAULT_STATION_PROFILE["p_rated"],
    ))

    # 创建历史决策记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS decision_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    decision_mode TEXT NOT NULL,
    net_profit REAL,
    total_throughput REAL,
    equivalent_cycles REAL,
    kpis_json TEXT
    )
    ''')
    market_columns = {
        "market_mode": "TEXT",
        "da_profit": "REAL",
        "sequential_profit": "REAL",
        "joint_profit": "REAL",
        "solver_name": "TEXT",
        "solver_status": "TEXT",
        "data_source": "TEXT",
    }
    existing_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(decision_records)")
    }
    for column, column_type in market_columns.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE decision_records ADD COLUMN {column} {column_type}"
            )
    conn.commit()
    conn.close()

def load_station_profile():
    """加载电站档案信息"""
    init_db()
    conn = get_db_connection()
    profile = conn.execute('SELECT * FROM station_profile WHERE id = 1').fetchone()
    conn.close()
    return dict(profile) if profile else None

def save_station_profile(profile_data):
    """保存或更新电站档案信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE station_profile
    SET station_name = ?, location = ?, commission_date = ?, e_rated = ?, p_rated = ?
    WHERE id = 1
    ''', (
        profile_data['station_name'],
        profile_data['location'],
        profile_data['commission_date'],
        profile_data['e_rated'],
        profile_data['p_rated']
    ))
    conn.commit()
    conn.close()

def save_decision_record(kpis, mode_text, market_metadata=None):
    """保存一条新的决策记录"""
    init_db()
    metadata = market_metadata or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO decision_records (
        run_timestamp, decision_mode, net_profit, total_throughput,
        equivalent_cycles, kpis_json, market_mode, da_profit,
        sequential_profit, joint_profit, solver_name, solver_status, data_source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        mode_text,
        kpis.get('总净利润', 0),
        kpis.get('总能量吞吐', 0),
        kpis.get('等效循环次数', 0),
        json.dumps(kpis),
        metadata.get("market_mode", "day_ahead_only"),
        metadata.get("da_profit", kpis.get('总净利润', 0)),
        metadata.get("sequential_profit"),
        metadata.get("joint_profit"),
        metadata.get("solver_name"),
        metadata.get("solver_status"),
        metadata.get("data_source"),
    ))
    conn.commit()
    conn.close()

def load_decision_records():
    """加载所有历史决策记录"""
    conn = get_db_connection()
    # 为避免因数据库文件损坏导致的潜在错误，使用 try-except 块
    try:
        records_df = pd.read_sql_query("SELECT * FROM decision_records ORDER BY run_timestamp DESC", conn)
    except pd.errors.DatabaseError:
        # 如果表不存在或损坏，返回一个空的DataFrame
        records_df = pd.DataFrame()
    finally:
        conn.close()
    return records_df
