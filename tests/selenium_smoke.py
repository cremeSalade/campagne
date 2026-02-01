from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1400,900')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get('http://127.0.0.1:8000/index.html')

        # Wait for app to load
        wait.until(lambda d: d.execute_script("return typeof window.searchCities === 'function';"))

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

        # Wait for results info
        wait.until(EC.presence_of_element_located((By.ID, 'results-info')))
        wait.until(lambda d: 'villes trouv' in d.find_element(By.ID, 'results-info').text)

        # Ensure results table has rows
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#results-list table tbody tr')))

        print('OK - selenium smoke test passed')
    except Exception as exc:
        try:
            driver.save_screenshot('tests/selenium_failure.png')
            with open('tests/selenium_failure.html', 'w', encoding='utf-8') as handle:
                handle.write(driver.page_source)
            print('Saved failure artifacts: tests/selenium_failure.png, tests/selenium_failure.html')
        except Exception:
            pass
        raise exc
    finally:
        # Print browser console logs for debugging
        try:
            for entry in driver.get_log('browser'):
                print(f"[browser] {entry.get('level')}: {entry.get('message')}")
        except Exception:
            pass
        driver.quit()


if __name__ == '__main__':
    main()
