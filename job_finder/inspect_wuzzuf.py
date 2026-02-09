
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

url = "https://wuzzuf.net/search/jobs/?key=3d%20artist&a=hpb"
try:
    response = requests.get(url, headers=headers)
    with open("wuzzuf_dump.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Dumped wuzzuf_dump.html")
except Exception as e:
    print(e)
