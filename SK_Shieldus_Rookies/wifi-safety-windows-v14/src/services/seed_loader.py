import csv, json, re, pathlib

ASSETS = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"

class RiskWeights(dict): __getattr__ = dict.get

def load_weights():
    with open(ASSETS/"risk_weights.json","r",encoding="utf-8") as f: return RiskWeights(json.load(f))
def load_oui():
    d={}
    with open(ASSETS/"oui_prefix.csv","r",encoding="utf-8") as f:
        for row in csv.DictReader(f): d[row["prefix"].upper()] = row["vendor"]
    return d
def load_patterns():
    pats=[]; kiosks=[]; cert=[]
    with open(ASSETS/"ssid_patterns.csv","r",encoding="utf-8") as f:
        for row in csv.DictReader(f): pats.append((row["name"], re.compile(row["regex"])))
    with open(ASSETS/"kiosk_vendors.csv","r",encoding="utf-8") as f:
        for row in csv.DictReader(f): kiosks.append((row["vendor"], re.compile(row["regex"])))
    with open(ASSETS/"certified_networks.csv","r",encoding="utf-8") as f:
        for row in csv.DictReader(f): cert.append(row)
    return pats, kiosks, cert
def load_demo():
    with open(ASSETS/"demo_logs.json","r",encoding="utf-8") as f: import json; return json.load(f)
