
def load_cookies():
    with open("cookies.txt", 'r') as f:
        return f.read()

class Config:
    CONCURRENCY = 100
    TIMEOUT = 100
    OUTPUT_FILE = "dickssportgoods-chunked.csv"
    COOKIE_FILE = "cookies.txt"
    HEADERS = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://www.dickssportinggoods.com',
        'priority': 'u=1, i',
        'referer': 'https://www.dickssportinggoods.com/p/nike-womens-dunk-low-shoes-23nikwdnklwwhtblcftwa/23nikwdnklwwhtblcftwa',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Cookie': load_cookies()
        }