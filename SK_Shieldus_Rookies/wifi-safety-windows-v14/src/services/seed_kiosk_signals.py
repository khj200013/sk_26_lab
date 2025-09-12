import sqlite3, os

def main():
    db = os.path.join("src", "whypie.db")
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS kiosk_signals(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      signal_type TEXT, pattern TEXT, role_hint TEXT, weight INTEGER, notes TEXT
    );
    """)
    rows = cur.execute("SELECT COUNT(*) FROM kiosk_signals").fetchone()[0]
    if rows == 0:
        cur.executemany(
            "INSERT INTO kiosk_signals(signal_type,pattern,role_hint,weight,notes) VALUES(?,?,?,?,?)",
            [
                ("ssid_keyword", r"(kiosk|키오스크|pos|테이블 ?오더|table ?order)", "kiosk", 15, "키오스크/주문"),
                ("ssid_keyword", r"(admin|관리자|staff)", "staff", 15, "관리/직원"),
            ],
        )
        con.commit()
        print("kiosk_signals seeded.")
    else:
        print("kiosk_signals already has data:", rows)
    con.close()

if __name__ == "__main__":
    main()
