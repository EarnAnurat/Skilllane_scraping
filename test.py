from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

options = webdriver.ChromeOptions()
options.add_argument('--headless')  # headless mode helps to run the script without opening the browser
service = Service(ChromeDriverManager().install())

# Using Selenium
driver = webdriver.Chrome(service=service, options=options)

template_url = 'https://futureskill.co/course?paginPage={}&course=all'

# Find the total number of total_pages
try:
    # open the URL
    driver.get(template_url.format(1))
    WebDriverWait(driver, 3).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'flex justify-center w-full'))
    )
    print("Page 1 is ready!")
except TimeoutException:
    print("Timeout while waiting for page 1 to load. Exiting.")
finally:
    soup = BeautifulSoup(driver.page_source, 'lxml')
    first_base_url_text = driver.page_source
    first_soup = BeautifulSoup(first_base_url_text, 'lxml')
    total_pages = first_soup.select('div[class="dark:text-neutralFS-50"]') # use select to specify the class
    if total_pages:
        total_pages = total_pages[0].text.split()[-1]
    
    # store data
    all_data = []

    # total_pages = 2  # Assuming there are 2 total_pages
    for page in range(1, int(total_pages)+1):
        print(f'total total_pages: {total_pages}')
        driver.get(template_url.format(page))
        try:
            WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'flex justify-center w-full'))
            )
            print(f"Page {page} is ready!")
        except TimeoutException:
            print(f"Timeout while waiting for page {page}. Skipping.")
            continue
        finally:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            course_names = soup.find_all('span', class_='text-grayFS-800 pt-[7px] line-clamp-2 css-6a9jn0')
            instructors = soup.find_all('div', class_='text-grayFS-800 css-t8kq3w e1b99tl71')
            prices = soup.find_all('div', class_='text-pinkFS-500')
            enrolleds_durations = soup.find_all('div', class_='text-neutralFS-300 css-19ne8l1 e1b99tl71')
            enrolleds = enrolleds_durations[::2]
            durations = enrolleds_durations[1::2]
            links = [a['href'] for a in soup.find_all('a', href=True)
                     if a.parent.name == 'div' and not a.parent.has_attr('class')
                     and "https://futureskill.co/course/detail/" in a['href']]

            for name, instructor, price, enrolled, duration, link in zip(course_names, instructors, prices, enrolleds, durations, links):
                driver.get(link)
                try:
                    WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, 'relative mb-5'))
                    )
                except TimeoutException:
                    # print(f"Timeout while waiting for course detail page {link}. Skipping.")
                    continue
                finally:
                    detail_text = BeautifulSoup(driver.page_source, 'lxml').find('div', class_='relative mb-5').get_text(strip=True)
                    # print(f'course_detail_soup: {BeautifulSoup(driver.page_source, "lxml")}')
                    # print(f'detail_text: {detail_text}')

                    all_data.append((name.text, instructor.text, price.text, enrolled.text, duration.text, link, detail_text))


    with open('course_details.txt', 'w', encoding='utf-8') as file:
        for name, instructor, price, enrolled, duration, link, detail in all_data:
            file.write(f'Course Name: {name}\nInstructor: {instructor}\nPrice: {price}\nEnrolled: {enrolled}\nDuration: {duration}\nLink: {link}\nDetail: {detail}\n\n')
    
    driver.quit()
