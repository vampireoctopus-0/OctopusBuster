# buster.py

from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import logging
import sys
import requests

class OctopusBuster:
    def __init__(self, target_url, wordlist_path, threads, extensions, output_file = None):
        self.target_url = target_url.rstrip('/')
        self.wordlist_path = wordlist_path
        self.threads = threads
        self.extensions = [f".{ext.strip().lstrip('.')}" for ext in extensions.split(',')] if extensions else [""]
        self.headers = {"user-Agent":"Octopus/1.1 (Production-GRADE CLI)"}

        # LOGGING INTERFACE SETUP
        self.logger = logging.getLogger("OctopusBuster")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s') # format ko clean rakhne k liye

        # screen 1 handler output screen pr show krwane k liye.
        screen_handler = logging.StreamHandler(sys.stdout)
        screen_handler.setFormatter(formatter)
        self.logger.addHandler(screen_handler)

        # screen2 File Handler if user gives -o flag
        if output_file:
            file_handler = logging.FileHandler(output_file, mode = 'w', encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)


    def run(self):
        # Ab har object logger use kary ga.!
        self.logger.info(f"[*] Target: {self.target_url}")
        self.logger.info(f"[*] Threads: {self.threads}")
        self.logger.info(f"[*] Extensions: {','.join(self.extensions) if self.extensions != [''] else None}")
        self.logger.info(f"{'FOUND PATH':<50} | {'STATUS':<10}")
        self.logger.info("-"*60)

        with ThreadPoolExecutor(max_workers = self.threads) as executor:
            futures = []
            for word in self.wordlist_loader():
                full_url = f"{self.target_url}/{word}"
                futures.append(executor.submit(self.check_url, full_url))

                if len(futures) >= self.threads * 2:
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            url, status = result
                            self.logger.info(f"{url:<50} | {status:<10}")
                    futures = []
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    url, status = result
                    self.logger.info(f"{url:<50} | {status:<10}")


    def wordlist_loader(self):
        # Memory Optimization: Puri ki puri file RAM pr load nai hogi. 1 line by line load hogi.
        try:
            with open(self.wordlist_path, "r", errors="ignore") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        for extension in [""] if not self.extensions else self.extensions:
                            yield f"{word}{extension}"
        except FileNotFoundError:
            self.logger.error(f"[!] ERROR--> File not found:{self.wordlist_path}")
            sys.exit(1)


    def check_url(self, full_url):
        # Low level HEAD request Factory
        try:
            response = requests.head(
                full_url,
                headers = self.headers,
                timeout= 3.0,
                allow_redirects=False
            )

            if response.status_code != 404:
                return full_url, response.status_code
        except requests.exceptions.RequestException:
            pass
        return None



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OctopusBuster v1.1")

    parser.add_argument("-u","--url", required=True, help="Need target url:")
    parser.add_argument("-w","--wordlist", required=True, help="worlist filepath is required.")
    parser.add_argument("-t", "--threads",type=int, default=10, help="Number of concurrent threads (default = 10)")
    parser.add_argument("-x", "--extensions", help="Extension must be seperated with commas.")
    parser.add_argument("-o", "--output", help="Output file path where output is save.")


    args = parser.parse_args()

    buster  = OctopusBuster(
        target_url = args.url,
        wordlist_path = args.wordlist,
        threads = args.threads,
        extensions = args.extensions,
        output_file = args.output
    )

    buster.run()