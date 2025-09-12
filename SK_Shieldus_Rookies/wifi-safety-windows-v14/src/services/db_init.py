# db_init.py
import os, sqlite3, time, pathlib

def get_db_path():
    # src/whypie.db 에 생성
    base = os.path.dirname(os.path.abspath(__file__))  
    return os.path.join(base, "whypie.db")

DDL = """
CREATE TABLE IF NOT EXISTS wifi_registry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  operator_name TEXT, venue_detail TEXT, city TEXT, district TEXT,
  facility_type TEXT, provider TEXT, ssid_pattern TEXT, install_ym TEXT,
  address_road TEXT, address_lot TEXT, managing_org TEXT, managing_tel TEXT,
  lat REAL, lon REAL, data_ref_date TEXT,
  intended_role TEXT, source TEXT, confidence INTEGER, last_verified_at TEXT
);
CREATE TABLE IF NOT EXISTS kiosk_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  signal_type TEXT, pattern TEXT, role_hint TEXT, weight INTEGER, notes TEXT
);
CREATE TABLE IF NOT EXISTS scan_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ssid TEXT, bssid TEXT, created_at TEXT, result_json TEXT
);
"""

def init_db():
    db = get_db_path()
    con = sqlite3.connect(db)
    con.executescript(DDL)
    con.commit()
    con.close()
    return db

if __name__ == "__main__":
    print("DB:", init_db())