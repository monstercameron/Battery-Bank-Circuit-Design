"""JLCPCB parts-library lookup (public search endpoint used by jlcpcb.com/parts).

Usage:
    python jlc.py "100nF 0402 50V"            # keyword search, top 10
    python jlc.py --code C1525                # exact part
Results are cached in jlc_cache.json so repeated runs don't hit the site.
"""
import json
import os
import sys
import time
import urllib.request

API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList/v2"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jlc_cache.json")
_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            with open(CACHE, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _save():
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(_cache, f, indent=0)


def _slim(d):
    attrs = {a.get("attribute_name_en"): a.get("attribute_value_name") for a in (d.get("attributes") or [])}
    prices = sorted(d.get("componentPrices") or [], key=lambda p: p["startNumber"])
    return {
        "code": d.get("componentCode"),
        "mpn": d.get("componentModelEn"),
        "brand": d.get("componentBrandEn"),
        "package": d.get("componentSpecificationEn"),
        "desc": d.get("describe"),
        "lib": d.get("componentLibraryType"),          # base = Basic, expand = Extended
        "preferred": bool(d.get("preferredComponentFlag")),
        "stock": d.get("stockCount") or 0,
        "price1": prices[0]["productPrice"] if prices else None,
        "attrs": attrs,
    }


def search(keyword, n=10, refresh=False):
    cache = _load()
    key = f"q:{keyword}:{n}"
    if key in cache and not refresh:
        return cache[key]
    body = json.dumps({"keyword": keyword, "currentPage": 1, "pageSize": n, "searchType": 2}).encode()
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"content-type": "application/json", "user-agent": "Mozilla/5.0 (parts lookup)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))
    lst = ((data.get("data") or {}).get("componentPageInfo") or {}).get("list") or []
    out = [_slim(d) for d in lst]
    cache[key] = out
    _save()
    time.sleep(0.6)
    return out


def part(code):
    for r in search(code, 5):
        if r["code"] == code:
            return r
    return None


def fmt(r):
    cls = "BASIC" if r["lib"] == "base" else ("PREF" if r["preferred"] else "ext")
    return f'{r["code"]:<10} {cls:<5} stk={r["stock"]:<9} ${r["price1"]!s:<8} {r["package"]!s:<14} {r["mpn"]!s:<28} {r["desc"]!s:.90}'


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--code":
        for c in args[1:]:
            r = part(c)
            print(fmt(r) if r else f"{c}: not found")
    else:
        for r in search(" ".join(args), 10):
            print(fmt(r))
