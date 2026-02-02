import os
import shutil
import glob
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    logging.basicConfig(level=logging.INFO, format='[e2e] %(message)s')
    log = logging.getLogger('e2e')

    cache_dir = os.path.join(os.path.dirname(__file__), ".selenium-cache")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["SELENIUM_MANAGER_CACHE_DIR"] = cache_dir
    os.environ["SELENIUM_CACHE_PATH"] = cache_dir
    os.environ["SE_CACHE_PATH"] = cache_dir
    os.environ["SELENIUM_MANAGER_DISABLE_STATISTICS"] = "1"
    os.environ["SE_DISABLE_REPORTING"] = "1"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1400,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--remote-debugging-port=0')
    options.add_argument(f"--user-data-dir={os.path.join(cache_dir, 'profile-e2e')}")
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    chrome_driver_path = (
        os.environ.get("CHROMEDRIVER_PATH")
        or shutil.which("chromedriver")
    )
    if not chrome_driver_path:
        candidates = glob.glob(os.path.join(cache_dir, "**", "chromedriver.exe"), recursive=True)
        if candidates:
            chrome_driver_path = candidates[0]

    if chrome_driver_path:
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    else:
        driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 25)

    def dump_browser_logs(prefix):
        try:
            entries = driver.get_log('browser')
            for entry in entries:
                log.info('%s browser %s: %s', prefix, entry.get('level'), entry.get('message'))
        except Exception as exc:
            log.info('%s browser logs unavailable: %s', prefix, exc)

    def dump_state(label):
        state = driver.execute_script(
            """
            const label = arguments[0];
            const rect = (el) => {
                if (!el) return null;
                const r = el.getBoundingClientRect();
                return { x: r.x, y: r.y, w: r.width, h: r.height };
            };
            const q = (sel) => document.querySelector(sel);
            return {
                label,
                url: window.location.href,
                viewport: { w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio },
                scroll: { x: window.scrollX, y: window.scrollY },
                doc: { sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth },
                tabsShell: rect(q('.tabs-shell')),
                resultsShell: rect(q('.results-shell')),
                stickyPanel: rect(q('.panel--sticky'))
            };
            """,
            label
        )
        log.info('STATE %s %s', label, json.dumps(state, ensure_ascii=False))

    def save_artifacts(prefix):
        driver.save_screenshot(f'tests/{prefix}.png')
        with open(f'tests/{prefix}.html', 'w', encoding='utf-8') as handle:
            handle.write(driver.page_source)

    try:
        log.info('open index')
        driver.get('http://127.0.0.1:8000/index.html')
        wait.until(lambda d: d.execute_script("return typeof window.searchCities === 'function';"))
        dump_state('index-ready')

        city_input = wait.until(EC.presence_of_element_located((By.ID, 'city-search')))
        for city in ['Lyon', 'Montpellier', 'Valence']:
            city_input.clear()
            city_input.send_keys(city)
            dropdown = wait.until(EC.presence_of_element_located((By.ID, 'autocomplete-dropdown')))
            wait.until(lambda d: 'hidden' not in dropdown.get_attribute('class'))
            dropdown.find_element(By.CSS_SELECTOR, 'li').click()
            city_input.send_keys(Keys.ESCAPE)

        min_pop = driver.find_element(By.ID, 'min-pop')
        max_pop = driver.find_element(By.ID, 'max-pop')
        min_pop.clear()
        min_pop.send_keys('2000')
        max_pop.clear()
        max_pop.send_keys('70000')

        search_button = driver.find_element(By.ID, "search-button")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
        driver.execute_script("arguments[0].click();", search_button)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#results-list table tbody tr')))
        dump_state('results-ready')

        # Switch tabs to validate UI
        for tab in ['map', 'urgences', 'urgences-map', 'list']:
            driver.execute_script("switchTab(arguments[0]);", tab)
            time.sleep(0.4)

        share_button = driver.find_element(By.XPATH, "//button[contains(., 'Sauvegarder')]")
        driver.execute_script("arguments[0].click();", share_button)
        share_input = wait.until(EC.presence_of_element_located((By.ID, 'share-link-inline')))
        share_url = share_input.get_attribute('value')
        if not share_url:
            raise AssertionError("Share link not generated")

        log.info('open share url %s', share_url)
        driver.get(share_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#results-list table tbody tr')))
        dump_state('share-results-ready')

        dump_browser_logs('final')
        log.info('OK - selenium e2e test passed')
    except Exception:
        save_artifacts('selenium_e2e_failure')
        dump_browser_logs('failure')
        raise
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
