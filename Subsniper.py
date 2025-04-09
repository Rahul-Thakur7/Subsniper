import requests
import re
import random
import threading
import queue
import argparse
import sys
import urllib3
from colorama import Fore, Style, init
from textwrap import wrap

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

TOOL_NAME = "SubSniper"
VERSION = "v2.0"
AUTHOR = "Rahul Thakur"
LINKEDIN = "https://www.linkedin.com/in/rahul-thakur7/"

mantras = [
    "ॐ नमो भगवते वासुदेवाय",
    "ॐ विष्णवे नमः",
    "ॐ नारायणाय विद्महे वासुदेवाय धीमहि तन्नो विष्णुः प्रचोदयात्",
    "ॐ श्री विष्णवे नमः"
]

vishnu_quotes = [
    {
        "verse": "Rig Veda 1.22.20",
        "shloka": "Vishnu is the one who pervades all space, the eternal, the ever-present, the supreme soul.",
        "translation": "Describes Vishnu’s omnipresence and eternal nature."
    },
    {
        "verse": "Rig Veda 1.154.2",
        "shloka": "Vishnu, who moves in a thousand ways, who spreads his light over the entire universe.",
        "translation": "Highlights his cosmic influence."
    },
    {
        "verse": "Yajur Veda 40.4",
        "shloka": "Vishnu is the supreme, the highest, the omnipotent, the infinite, the one who sustains all.",
        "translation": "Vishnu as the omnipotent sustainer of all."
    },
    {
        "verse": "Taittiriya Aranyaka 3.12",
        "shloka": "He is the Supreme Vishnu, eternal, pervading all things.",
        "translation": "Source of all creation and existence."
    },
    {
        "verse": "Atharva Veda 10.8.7",
        "shloka": "Vishnu, the eternal, pervades everything; the one who nourishes the universe.",
        "translation": "Refers to Vishnu’s nourishing power."
    },
]

def get_spiritual_line():
    if random.choice([True, False]):
        return random.choice(mantras)
    else:
        quote = random.choice(vishnu_quotes)
        return f"{quote['shloka']} - {quote['translation']} ({quote['verse']})"

def print_banner():
    spiritual_line = get_spiritual_line()
    ascii_art = r"""
     _________.__              .___                   .__              
    /   _____/|  |__  __ __  __| _/____ _______  _____|  |__ _____    ____  
    \_____  \ |  |  \|  |  \/ __ |\__  \_  __ \/  ___/  |  \__  \  /    \ 
    /        \|   Y  \  |  / /_/ | / __ \|  | \/\___ \|   Y  \/ __ \|   |  \
   /_______  /|___|  /____/\____ |(____  /__|  /____  >___|  (____  /___|  /
           \/      \/           \/     \/           \/     \/     \/     \/"""

    print(Fore.RED + ascii_art + "\n")
    print(Fore.YELLOW + f"       {TOOL_NAME} {VERSION} " + Fore.CYAN + "🕉️\n")

    wrapped_lines = wrap(spiritual_line, width=75)
    for line in wrapped_lines:
        print(Fore.MAGENTA + f"       {line}")

    print(Fore.GREEN + f"\n       By {AUTHOR} | LinkedIn: {LINKEDIN}\n")


def fetch_subdomains(domain):
    sources = [crtsh, threatcrowd, anubis, wayback_machine, hackertarget]
    found = set()
    print(f"[+] Passive scan on {domain}\n")
    for source in sources:
        try:
            result = source(domain)
            found.update(result)
        except Exception as e:
            print(f"[-] Error with {source.__name__}: {e}")
    print(f"[+] Total subdomains found: {len(found)}")
    return list(found)


def crtsh(domain):
    print("[*] Fetching from crt.sh...")
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        res = requests.get(url, timeout=10)
        json_data = res.json()
        return {entry['name_value'].lower() for entry in json_data}
    except:
        return set()


def threatcrowd(domain):
    print("[*] Fetching from ThreatCrowd...")
    url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}"
    res = requests.get(url, timeout=10)
    return set(res.json().get("subdomains", []))


def anubis(domain):
    print("[*] Fetching from Anubis...")
    url = f"https://jldc.me/anubis/subdomains/{domain}"
    res = requests.get(url, timeout=10)
    return set(res.json())


def wayback_machine(domain):
    print("[*] Fetching from WaybackMachine...")
    url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=text&fl=original&collapse=urlkey"
    res = requests.get(url, timeout=10)
    return {re.findall(r"https?://([a-zA-Z0-9_.-]+)", line)[0] for line in res.text.splitlines() if re.findall(r"https?://([a-zA-Z0-9_.-]+)", line)}


def hackertarget(domain):
    print("[*] Fetching from HackerTarget...")
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    res = requests.get(url, timeout=10)
    return {line.split(',')[0] for line in res.text.splitlines() if ',' in line}


def is_live(subdomain):
    for proto in ["https://", "http://"]:
        try:
            res = requests.get(proto + subdomain, timeout=4, verify=False)
            if res.status_code < 400:
                return True
        except:
            continue
    return False


def check_live_subdomains(subdomains, thread_count):
    print("[*] Checking for LIVE websites only...\n")
    live = []
    q = queue.Queue()

    def worker():
        while True:
            sub = q.get()
            if is_live(sub):
                print(f"{Fore.GREEN}[LIVE] {sub}")
                live.append(sub)
            q.task_done()

    for _ in range(thread_count):
        threading.Thread(target=worker, daemon=True).start()

    for sub in subdomains:
        q.put(sub)

    q.join()
    return live


def main():
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} - Subdomain Live Finder")
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Threads (default: 50)")
    args = parser.parse_args()

    print_banner()
    domain = args.domain.strip().lower().replace("http://", "").replace("https://", "").rstrip('/')
    found = fetch_subdomains(domain)
    live = check_live_subdomains(found, args.threads)

    print(f"\n[+] Accessible websites found: {len(live)}")
    for l in live:
        print(f"✔ {l}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Interrupted by user. Exiting...")
        sys.exit(0)
