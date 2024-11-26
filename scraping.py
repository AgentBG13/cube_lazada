import time
from seleniumbase import Driver
from selenium.webdriver.common.by import By
import pandas as pd
import random


def clean_mvs(data):
    def parse_value(item):
        if item == '':
            return None 
        if isinstance(item, str):
            return float(item.replace('Rp', '').strip())
        return float(item)

    return [parse_value(item) for item in data]


def clean_num_reviews(data):
    def parse_value(item):
        if isinstance(item, str):
            # Remove parentheses and convert to integer
            item = item.replace('(', '').replace(')', '').strip()
            return int(item)
        return int(item)

    return [parse_value(item) for item in data]


def clean_num_solds(data):
    def parse_value(item):
        if isinstance(item, str):
            # Remove "sold" and process the numeric part
            item = item.replace(' sold', '').strip()
            if 'K' in item:
                return float(item.replace('K', '')) * 1000
            else:
                return float(item)
        return float(item)

    return [parse_value(item) for item in data]


def run():
    timeout = 5
    url = 'https://www.lazada.co.id/esqa-cosmetics/?q=All-Products&from=wangpu&langFlag=en&pageTypeId=2'

    driver = Driver(uc=True)
    driver.uc_open_with_reconnect(url)
    driver.maximize_window()
    driver.reconnect(timeout=timeout)

    # Get all product features
    products = []
    nmvs = []
    gmvs = []
    num_solds = []
    num_reviews = []

    for elem in driver.find_elements(By.XPATH, '//div[@data-qa-locator="product-item"]'):
        products.append(elem.find_element(By.XPATH, './div/div/div[2]/div[2]/a').get_attribute('title'))
        nmvs.append(elem.find_element(By.XPATH, './div/div/div[2]/div[3]/span').text)
        
        gmvs.append(elem.find_element(By.XPATH, './div/div/div[2]/div[4]/span[1]/del').text if elem.find_elements(By.XPATH, './div/div/div[2]/div[4]/span[1]/del') else '')
        
        num_solds.append(elem.find_element(By.XPATH, './div/div/div[2]/div[5]/span[1]/span').text if elem.find_elements(By.XPATH, './div/div/div[2]/div[5]/span[1]/span') else 0.0)
        
        num_reviews.append(elem.find_element(By.XPATH, './div/div/div[2]/div[5]/div/span').text if elem.find_elements(By.XPATH, './div/div/div[2]/div[5]/div/span') else 0.0)
    
    nmvs = clean_mvs(nmvs)
    gmvs = clean_mvs(gmvs)
    num_reviews = clean_num_reviews(num_reviews)
    num_solds = clean_num_solds(num_solds)

    data = {
        'product': products,
        'nmv': nmvs,
        'gmv': gmvs,
        'num_sold': num_solds,
        'num_reviews': num_reviews
    }

    df = pd.DataFrame(data)

    # Assign back nmv to gmv if gmv is missing
    df.loc[df['gmv'].isnull(), 'gmv'] = df.loc[df['gmv'].isnull(), 'nmv']

    # Get top5 best selling products, to scrape the reviews for the year 2024
    top5 = df.nlargest(5, 'num_sold')['product'].tolist()

    driver.quit()
    df_2024 = pd.DataFrame()
    for prod in top5:
        print(f'Scraping reviews for {prod}')
        print('---------------------------------')
        time.sleep(180 + random.uniform(0, 25))
        driver.uc_open_with_reconnect(url)
        try:
            driver.js_click(f'//*[text()="{prod}"]', timeout=10)
        except:
            print('TimeoutError, Ignoring...')
        
        # Scroll to the reviews section
        driver.execute_script("window.scrollBy(0, 1500);")
        # Use random to avoid bot detection
        driver.reconnect(timeout=random.uniform(0, 5.5))
        driver.js_click("//*[contains(text(), 'Urutkan')]")
        driver.reconnect(timeout=random.uniform(0, 5.5))
        driver.js_click("//ul[@class='next-menu-content']/li[2]")
        driver.reconnect(timeout=random.uniform(0, 5.5))

        # Scrape reviews
        review_dates = []
        review_authors = []

        # Bug out after 200 review pages, can't get any further
        for i in range(100):
            stop = False
            for elem in driver.find_elements(By.CLASS_NAME, "item")[1:]:
                driver.reconnect(timeout=random.uniform(0, 1.0))
                try:
                    text1 = elem.find_element(By.CLASS_NAME, "top")
                    if text1.text.find('2024') == -1 and i > 20:
                        stop = True
                        break
                    review_dates.append(text1.text)
                    text2 = elem.find_element(By.CLASS_NAME, "middle")
                    review_authors.append(text2.find_element(By.TAG_NAME, "span").text)
                except:
                    pass
            if stop:
                break
            driver.reconnect(timeout=random.uniform(0, 5.5))
            # Scroll to the next page
            driver.execute_script("window.scrollBy(0, 600);")
            driver.reconnect(timeout=random.uniform(0, 5.5))
            # Click next page
            driver.js_click('//*[@id="module_product_review"]/div/div/div[3]/div[2]/div/button[2]')
            driver.reconnect(timeout=random.uniform(0, 5.5))

        data = {
            'name': prod,
            'review_dates': review_dates,
            'review_authors': review_authors
        }

        temp = pd.DataFrame(data)
        df_2024 = pd.concat([df_2024, temp], axis=0)
        driver.quit()

    driver.quit()
    return df, df_2024


if __name__ == '__main__':
    run()