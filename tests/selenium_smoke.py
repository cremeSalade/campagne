#!/usr/bin/env python
#  type: ignore

import os
import shutil
import glob
import json
import time
import logging
from selenium import webdriver # type: ignore
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    logging.basicConfig(level=logging.INFO, format='[selenium] %(message)s')
    log = logging.getLogger('selenium')

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
    options.add_argument(f'--user-data-dir={os.path.join(cache_dir, "profile")}')
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
    wait = WebDriverWait(driver, 20)

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
                tabs: rect(q('.tabs')),
                tabsLeft: rect(q('.tabs-shell .scroll-indicator--left')),
                tabsRight: rect(q('.tabs-shell .scroll-indicator--right')),
                resultsShell: rect(q('.results-shell')),
                resultsList: rect(q('#results-list')),
                resultsLeft: rect(q('.results-shell .scroll-indicator--left')),
                resultsRight: rect(q('.results-shell .scroll-indicator--right')),
                stickyPanel: rect(q('.panel--sticky'))
            };
            """
        )
        log.info('STATE %s %s', label, json.dumps(state, ensure_ascii=False))

    def save_artifacts(prefix):
        driver.save_screenshot(f'tests/{prefix}.png')
        with open(f'tests/{prefix}.html', 'w', encoding='utf-8') as handle:
            handle.write(driver.page_source)

    try:
        log.info('open index')
        driver.get('http://127.0.0.1:8000/index.html')

        # Wait for app to load
        wait.until(lambda d: d.execute_script("return typeof window.searchCities === 'function';"))
        dump_state('index-ready')

        # Autocomplete input
        city_input = wait.until(EC.presence_of_element_located((By.ID, 'city-search')))
        city_input.clear()
        city_input.send_keys('Paris')

        # Wait for dropdown and click first suggestion
        dropdown = wait.until(EC.presence_of_element_located((By.ID, 'autocomplete-dropdown')))
        wait.until(lambda d: 'hidden' not in dropdown.get_attribute('class'))
        first_item = dropdown.find_element(By.CSS_SELECTOR, 'li')
        first_item.click()
        # Try to close dropdown to avoid click interception
        city_input.send_keys(Keys.ESCAPE)
        driver.execute_script("document.body.click();")
        dump_state('autocomplete-selected')

        # Set population range
        min_pop = driver.find_element(By.ID, 'min-pop')
        max_pop = driver.find_element(By.ID, 'max-pop')
        min_pop.clear()
        min_pop.send_keys('5000')
        max_pop.clear()
        max_pop.send_keys('50000')

        # Trigger search
        search_button = driver.find_element(By.ID, "search-button")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
        driver.execute_script("arguments[0].click();", search_button)
        dump_browser_logs('after-click')

        # Wait for results info
        wait.until(EC.presence_of_element_located((By.ID, 'results-info')))
        wait.until(lambda d: 'villes trouv' in d.find_element(By.ID, 'results-info').text)
        dump_state('results-ready')

        # Ensure results table has rows
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#results-list table tbody tr')))

        def check_overflow(label, width, height, zoom, prefix):
            driver.set_window_size(width, height)
            driver.execute_script("document.documentElement.style.zoom = arguments[0];", zoom)
            driver.save_screenshot(f'tests/{prefix}_{label}.png')
            return driver.execute_script(
                """
                const doc = document.documentElement;
                const overflow = doc.scrollWidth > doc.clientWidth;
                if (!overflow) return { overflow: false, offenders: [] };
                const offenders = [];
                const elements = Array.from(document.querySelectorAll('*'));
                for (const el of elements) {
                    if (!el || !el.getBoundingClientRect) continue;
                    const sw = el.scrollWidth;
                    const cw = el.clientWidth;
                    if (sw > cw + 2) {
                        const rect = el.getBoundingClientRect();
                        offenders.push({
                            tag: el.tagName,
                            id: el.id || null,
                            className: el.className || null,
                            scrollWidth: sw,
                            clientWidth: cw,
                            rectWidth: rect.width
                        });
                        if (offenders.length >= 8) break;
                    }
                }
                return { overflow: true, offenders };
                """
            )

        scenarios = [
            ("1080x2400", 1080, 2400, "1"),
            ("390x844_zoom125", 390, 844, "1.25"),
            ("360x800_zoom15", 360, 800, "1.5"),
        ]

        for label, w, h, z in scenarios:
            result = check_overflow(label, w, h, z, "overflow_main")
            if result.get("overflow"):
                dump_state(f'overflow-main-{label}')
                raise AssertionError(f"Page overflow detected on main results page ({label}): {result.get('offenders')}")

        share_button = driver.find_element(By.XPATH, "//button[contains(., 'Sauvegarder')]")
        driver.execute_script("arguments[0].click();", share_button)
        share_input = wait.until(EC.presence_of_element_located((By.ID, 'share-link-inline')))
        share_url = share_input.get_attribute('value')
        if not share_url:
            raise AssertionError("Share link not generated")

        log.info('open share url %s', share_url)
        driver.get(share_url)
        wait.until(EC.presence_of_element_located((By.ID, 'results-list')))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#results-list table tbody tr')))
        dump_state('share-results-ready')

        def check_overflow_saved(label, width, height, zoom):
            return check_overflow(label, width, height, zoom, "overflow_saved")

        for label, w, h, z in scenarios:
            result = check_overflow_saved(label, w, h, z)
            if result.get("overflow"):
                dump_state(f'overflow-saved-{label}')
                raise AssertionError(f"Page overflow detected on saved results page ({label}): {result.get('offenders')}")

        log.info('OK - selenium smoke test passed')
    except Exception as exc:
        try:
            save_artifacts('selenium_failure')
            log.info('Saved failure artifacts: tests/selenium_failure.png, tests/selenium_failure.html')
        except Exception:
            pass
        raise exc
    finally:
        # Print browser console logs for debugging
        try:
            for entry in driver.get_log('browser'):
                log.info("[browser] %s: %s", entry.get('level'), entry.get('message'))
        except Exception:
            pass
        driver.quit()


if __name__ == '__main__':
    main()
