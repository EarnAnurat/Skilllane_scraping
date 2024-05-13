from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import concurrent.futures
import csv

def setup_driver():
    """Sets up the Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # not opening the browser
    options.add_argument('--no-sandbox')  # Bypass OS security model, necessary for certain environments
    options.add_argument('--disable-gpu')  # Disables GPU hardware acceleration, necessary for headless
    options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppresses certain logs
    service = Service(ChromeDriverManager().install()) # automatically manage the driver version
    driver = webdriver.Chrome(service=service, options=options) # initialize the driver
    return driver

def find_total_pages(driver):
    """Finfs the total number of pages for scraping."""
    url = 'https://futureskill.co/course?paginPage=1&course=all'
    driver.get(url)
    try:
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'flex justify-center w-full'))
        )
    except TimeoutException:
        print("Failed to load first page or find the pagination info.")
    finally:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        pages = soup.select('div[class="dark:text-neutralFS-50"]')  # <div class="dark:text-neutralFS-50">/ 42</div>
        if pages:
            print(f"Total pages: {pages[0].text.split()[-1]}")
            return int(pages[0].text.split()[-1])

def scrape_detail_page(driver, url):
    """Scrape detailed info from a course detail page."""
    # url = "https://futureskill.co/course/detail/1014"
    try:
        driver.get(url)
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'relative mb-5'))
        )
    except TimeoutException:
        print(f"Timeout while waiting for course detail page {url}. continue.")
    finally:
        detail_soup = BeautifulSoup(driver.page_source, 'lxml')
        print(f"Getting detail for {url}")
        detail_text = detail_soup.find('div', class_='relative mb-5').get_text(strip=True)
        # print(detail_text)
        return detail_text
    
def scrape_page(page):
    """Scrape a page of https://futureskill.co/course?paginPage={}&course=all"""
    driver = setup_driver()
    data = []
    try:
        url = f'https://futureskill.co/course?paginPage={page}&course=all'
        driver.get(url)
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'flex justify-center w-full'))
        )
        print(f"Page {page} is ready.")
    except TimeoutException:
        print(f"Timeout while waiting for page {page}. continue.")
    finally:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        print(f"Scraping page {page}")
        courses = soup.find_all('div', class_='flex justify-center w-full')
        for course in courses:
            course_name = course.find('span', class_='text-grayFS-800 pt-[7px] line-clamp-2 css-6a9jn0')
            instructor = course.find('div', class_='text-grayFS-800 css-t8kq3w e1b99tl71')
            price = course.find('div', class_='text-pinkFS-500')
            enrolled_durations = course.find_all('div', class_='text-neutralFS-300 css-19ne8l1 e1b99tl71')
            enrolled = enrolled_durations[0].text
            duration = enrolled_durations[1].text
            link = [a['href'] for a in course.find_all('a', href=True)
                     if a.parent.name == 'div' 
                     and not a.parent.has_attr('class')
                     and "https://futureskill.co/course/detail/" in a['href']][0]
            detail_text = scrape_detail_page(driver, link)
            print(f"course_name: {course_name.text}, instructor: {instructor.text}, price: {price.text}, enrolled: {enrolled}, duration: {duration}, link: {link}, detail_text: {detail_text}")
            data.append((course_name, instructor, price, enrolled, duration, link, detail_text))

        driver.quit()
        return data

def main():
    driver = setup_driver()
    total_pages = find_total_pages(driver)
    driver.quit() # close the browser for total_pages function
    with concurrent.futures.ThreadPoolExecutor(max_workers= 2) as executor:
        futures = [executor.submit(scrape_page, page) for page in range(1, total_pages + 1)]
        results = []
        for future in futures:
            results.extend(future.result())
    
    # Save results to a csv
    with open('course_details.csv', 'w', newline='',encoding='utf-8') as file:
        writer = csv.writer(file)
        # header
        writer.writerow(['Course Name', 'Instructor', 'Price', 'Enrolled', 'Duration', 'Link', 'Detail'])
        # write data

        for (course_name, instructor, price, enrolled, duration, link, detail_text) in results:
            writer.writerow([course_name.text, instructor.text, price.text, enrolled, duration, link, detail_text])

if __name__ == '__main__':
    main()
