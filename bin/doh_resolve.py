#!/usr/bin/env python3
import json, sys, urllib.request

# Cloudflare DoH JSON endpoint
DOH = "https://cloudflare-dns.com/dns-query?name={name}&type=A"

def doh_a(name: str) -> list[str]:
    url = DOH.format(name=name)
    req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    ips = []
    for ans in data.get("Answer", []) or []:
        if ans.get("type") == 1 and isinstance(ans.get("data"), str):
            ips.append(ans["data"])
    return ips

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "imap.gmail.com"
    ips = doh_a(host)
    if not ips:
        print("")
        sys.exit(2)
    print(ips[0])
