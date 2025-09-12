
import argparse, json, csv
from services.seed_loader import load_weights, load_oui, load_patterns, load_demo
from services.scanner import scan
from services.score_engine_db import score_entry
from utils.pretty_print import print_table

def main():
    ap = argparse.ArgumentParser(description="Wi‑Fi Safety (CLI)")
    ap.add_argument("--json", help="출력을 JSON으로 저장")
    ap.add_argument("--csv", help="출력을 CSV로 저장")
    ap.add_argument("--demo", action="store_true", help="스캔 대신 데모 데이터 사용")
    args = ap.parse_args()

    weights = load_weights(); oui = load_oui(); ssid_pats, kiosk, certified = load_patterns()
    items = load_demo() if args.demo else scan()
    if not items:
        print("스캔 결과가 없거나 권한/도구가 없습니다. --demo 옵션을 사용해 보세요.")
        return
    scored = [score_entry(it, weights, oui, ssid_pats, certified) for it in items]
    if not (args.json or args.csv):
        print_table(scored)
    if args.json:
        with open(args.json,"w",encoding="utf-8") as f: json.dump(scored,f,ensure_ascii=False,indent=2); print("JSON 저장:", args.json)
    if args.csv:
        keys = ["ssid","bssid","score","grade","reasons","capabilities","signal","channel","vendor"]
        with open(args.csv,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
            for r in scored:
                row = {k: r.get(k,"") for k in keys}; row["reasons"] = " | ".join(r.get("reasons",[])); w.writerow(row)
        print("CSV 저장:", args.csv)

if __name__ == "__main__":
    main()
