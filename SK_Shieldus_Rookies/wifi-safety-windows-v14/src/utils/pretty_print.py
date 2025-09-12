def print_table(rows):
    if not rows:
        print("(표시할 항목 없음)"); return
    headers = ["SSID","점수","등급","이유"]
    data = [[r["ssid"], r["score"], r["grade"], " · ".join(r.get("reasons",[]))] for r in rows]
    widths = [max(len(str(x)) for x in col) for col in zip(*([headers]+data))]
    def fmt(row): return "  ".join(str(val).ljust(widths[i]) for i,val in enumerate(row))
    print(fmt(headers)); print("-"*(sum(widths)+2*(len(widths)-1)))
    for row in data: print(fmt(row))
