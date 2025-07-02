import requests
from datetime import datetime, timedelta

# ------------------ CONFIG -------------------
USER_AGENT = "K Chi kchi7490@gmail.com"
MAX_RESULTS_PER_QUERY = 50
RECENT_HOURS = 2
FORMS = ["8-K", "6-K", "S-1", "F-1", "10-K", "10-Q"]
KEYWORDS = ["crypto", "bitcoin", "ethereum", "solana"]
# ---------------------------------------------

headers = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate"
}

today = datetime.utcnow().date()
start_date = today - timedelta(days=2)
now_utc = datetime.utcnow()
recent_cutoff = now_utc - timedelta(hours=RECENT_HOURS)

def run_search(query, startdt, enddt):
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": query,
        "startdt": startdt.isoformat(),
        "enddt": enddt.isoformat(),
        "from": "0",
        "size": str(MAX_RESULTS_PER_QUERY)
    }

    try:
        print(f"⏱️ Searching: '{query}' from {params['startdt']} to {params['enddt']}")
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json().get("hits", {}).get("hits", [])
    except Exception as e:
        print(f"❌ Failed search for '{query}': {e}")
        return []

def fetch_and_match_all(startdt, enddt):
    seen = set()
    recent_matches = []
    older_matches = []

    print(f"\n🔍 Running crypto+form EDGAR searches from {startdt} through {enddt}...\n")

    for form in FORMS:
        for keyword in KEYWORDS:
            query = f"{form} {keyword}"
            hits = run_search(query, startdt, enddt)

            for r in hits:
                try:
                    src = r["_source"]
                    accession = src["adsh"]
                    if accession in seen:
                        continue

                    filed_at = src.get("filedAt", "")
                    filed_time = None
                    if filed_at:
                        try:
                            filed_time = datetime.fromisoformat(filed_at.replace("Z", "+00:00"))
                        except Exception:
                            pass

                    cik = str(src["ciks"][0]).zfill(10)
                    form_type = src.get("form", "")
                    entity = src.get("display_names", ["Unknown"])[0]
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}-index.htm"
                    raw_url = filing_url.replace("-index.htm", ".txt")

                    res = requests.get(raw_url, headers=headers)
                    text = res.text.lower()
                    if keyword.lower() not in text:
                        continue

                    match = {
                        "accession": accession,
                        "form": form_type,
                        "entity": entity,
                        "url": filing_url,
                        "filed_at_dt": filed_time
                    }

                    if filed_time and filed_time > recent_cutoff:
                        recent_matches.append(match)
                    else:
                        older_matches.append(match)

                    seen.add(accession)

                except Exception as e:
                    print(f"⚠️ Error processing result: {e}")
                    continue

    def safe_sort_key(x):
        dt = x.get("filed_at_dt")
        return dt if isinstance(dt, datetime) else datetime.min

    recent_matches.sort(key=safe_sort_key, reverse=True)
    older_matches.sort(key=safe_sort_key, reverse=True)

    return recent_matches, older_matches

def print_matches(header, matches):
    if not matches:
        return
    print(f"\n===== {header} ({len(matches)}) =====\n")
    for m in matches:
        print(f"📄 Form: {m['form']}")
        print(f"🏢 Entity: {m['entity']}")
        print(f"🔗 Link: {m['url']}\n")

if __name__ == "__main__":
    recent, older = fetch_and_match_all(start_date, today)

    if not recent and not older:
        print("\n❌ No matches found.")
    else:
        print_matches("🆕 RECENT FILINGS (last 2 hours)", recent)
        print_matches("📁 ALL OTHER FILINGS", older)