import argparse
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def run_test(test_type):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        if test_type == "regular":
            print("Starting Regular Test: Opening 4 static pages...")
            urls = ["https://example.com"] * 4
        else:
            print("Starting Heavy JS Test: Opening 4 heavy sites...")
            urls = [
                "https://webglsamples.org/",
                "https://threejs.org/examples/",
                "https://www.google.com/maps",
                "https://www.youtube.com",
            ]

        # Open 4 tabs
        for i, url in enumerate(urls):
            if i == 0:
                driver.get(url)
            else:
                driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(2)

        print("Test running. Recording data for 30 seconds...")
        time.sleep(30)

    finally:
        driver.quit()
        print(f"{test_type.capitalize()} test finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["regular", "heavy"], required=True)
    args = parser.parse_args()

    run_test(args.type)
