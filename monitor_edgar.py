import requests
from bs4 import BeautifulSoup

# ------------------ CONFIG -------------------
USER_AGENT = "K Chi kchi7490@gmail.com"
KEYWORD_FILE = "keywords.txt"
MAX_FILINGS = 50  # You can raise this if needed
# ---------------------------------------------

# Load keywords
with open(KEYWORD_FILE, "r") as f:
    keywords = [line.strip().lower() for line in f if line.strip()]

headers = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate"
}

# Get recent filings from EDGAR full-text search
def get_recent_filings():
    url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": "",  # no form restriction
        "from": "0",
        "size": str(MAX_FILINGS)
    }

    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"❌ Failed to fetch filings: {res.status_code}")
        return []

    results = res.json().get("hits", {}).get("hits", [])
    filings = []
    for r in results:
        try:
            src = r["_source"]
            accession = src["adsh"]
            cik = str(src["ciks"][0]).zfill(10)
            form = src.get("form", "")
            entity = src.get("display_names", ["Unknown"])[0]
            description = src.get("title", "No description provided.")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{accession}-index.htm"

            filings.append({
                "url": filing_url,
                "cik": cik,
                "form": form,
                "entity": entity,
                "description": description,
                "accession": accession
            })
        except:
            continue
    return filings

# Scan each filing for keyword matches
def scan_filings(filings):
    matches = []
    for filing in filings:
        raw_url = filing["url"].replace("-index.htm", ".txt")
        try:
            res = requests.get(raw_url, headers=headers)
            text = res.text.lower()
            for kw in keywords:
                if kw in text:
                    print(f"\n✅ Match: '{kw}'")
                    print(f"📄 Form: {filing['form']}")
                    print(f"🏢 Entity: {filing['entity']}")
                    print(f"📝 Description: {filing['description']}")
                    print(f"🔗 Link: {filing['url']}")
                    matches.append({**filing, "keyword": kw})
                    break
        except Exception as e:
            print(f"⚠️ Error reading {raw_url}: {e}")
    return matches

if __name__ == "__main__":
    print("🔍 Searching all recent SEC filings for keyword matches...")
    filings = get_recent_filings()
    if not filings:
        print("No filings found.")
    else:
        scan_filings(filings)