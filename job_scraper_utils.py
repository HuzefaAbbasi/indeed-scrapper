import os
import random
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

global total_jobs


def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]
    return random.choice(user_agents)


def configure_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={get_random_user_agent()}")
    options.add_argument('--disable-popup-blocking')
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            run_on_insecure_origins=True
            )
    return driver


def search_jobs(driver, country, job_position, job_location, date_posted):
    full_url = f'{country}/jobs?q={"+".join(job_position.split())}&l={job_location}&fromage={date_posted}'
    print(full_url)
    driver.get(full_url)
    global total_jobs
    time.sleep(random.uniform(3, 7))

    try:
        job_count_element = driver.find_element(By.XPATH,
                                                '//div[starts-with(@class, "jobsearch-JobCountAndSortPane-jobCount")]')

        total_jobs = job_count_element.find_element(By.XPATH, './span').text
        print(f"{total_jobs} found")
    except NoSuchElementException:
        print("No job count found")
        total_jobs = "Unknown"

    # driver.save_screenshot('screenshot.png')
    return full_url


def scrape_job_data(driver, country):
    job_count = 0
    if not os.path.exists('job_pages'):
        os.makedirs('job_pages')
    count = 0
    while True:

        soup = BeautifulSoup(driver.page_source, 'lxml')

        boxes = soup.find_all('div', class_='job_seen_beacon')

        for index, box in enumerate(boxes):
            # Get the link to the full job page
            link = box.find('a').get('href')
            link_full = country + link

            # Open the link in a new tab
            driver.execute_script("window.open('');")
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[1])
            driver.get(link_full)
            time.sleep(random.uniform(3, 7))
            with open(f'job_pages/job_page{count+index}.html', 'w', encoding='utf-8') as f:
                f.write(BeautifulSoup(driver.page_source, 'lxml').prettify())

            # Close the tab and switch back to the original tab
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(random.uniform(1, 3))

            job_count += 1

        print(f"Scraped {job_count} of {total_jobs}")
        count = job_count

        try:
            next_page = soup.find('a', {'aria-label': 'Next Page'}).get('href')

            next_page = country + next_page
            driver.get(next_page)
            time.sleep(random.uniform(2, 5))

        except:
            print("Some Error Occurred")
            break


def read_job_pages():
    # Initialize an empty list to store job details
    job_data = []

    # Loop over all files in the job_pages directory
    for file_name in os.listdir('job_pages'):
        if file_name.endswith('.html'):
            # Read the content of each file
            with open(os.path.join('job_pages', file_name), 'r', encoding='utf-8') as f:
                page_content = f.read()

            # Parse the content with BeautifulSoup
            soup = BeautifulSoup(page_content, 'lxml')

            # Extract the job title
            job_title = soup.find('div', class_='jobsearch-JobInfoHeader-title-container')
            job_title = job_title.find('span').text.strip() if job_title else 'N/A'
            # print(job_title)

            # Extract the company name
            company = soup.find('div', {'data-testid': 'inlineHeader-companyName'})
            company = company.find('a').text.strip() if company and company.find('a') else 'N/A'
            # print(company)

            # Extract the company location
            location = soup.find('div', {'data-testid': 'inlineHeader-companyLocation'})
            location = location.text.strip() if location else 'N/A'
            # print(location)

            # Extract the salary (if available)
            salary = soup.find('div', {'id': 'salaryInfoAndJobType'})
            salary = salary.find('span').text.strip() if salary else 'N/A'
            # print(salary)

            # Extract the job type
            job_type = soup.find('div', {'aria-label': 'Job type'})
            # print(job_type)
            if job_type:
                job_types =[item.get_text(strip=True) for item in job_type.find_all('li')]
                # print(job_types)



            # Extract the job description
            job_description = soup.find('div', {'id': 'jobDescriptionText'})
            job_description = job_description.text.strip() if job_description else 'N/A'
            # print(job_description)

            date_posted = datetime.now().date()
            # Append the extracted data to the job_data list
            job_data.append({
                'Job Title': job_title,
                'Company': company,
                'Location': location,
                'Salary': salary,
                'Job Type': job_types,
                'Description': job_description,
                'Date Posted': date_posted
            })

    # Create a pandas DataFrame from the job_data list
    df = pd.DataFrame(job_data)

    return df


def delete_job_pages_files():
    folder_path = 'job_pages'

    # Check if the folder exists
    if os.path.exists(folder_path):
        # Iterate over all the files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            # Check if it is a file and delete it
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("All files deleted successfully.")
    else:
        print(f"Folder '{folder_path}' does not exist.")


# def clean_data(df):
#     def posted(x):
#         x = x.replace('PostedPosted', '').strip()
#         x = x.replace('EmployerActive', '').strip()
#         x = x.replace('PostedToday', '0').strip()
#         x = x.replace('PostedJust posted', '0').strip()
#         x = x.replace('today', '0').strip()
#
#         return x
#
#     def day(x):
#         x = x.replace('days ago', '').strip()
#         x = x.replace('day ago', '').strip()
#         return x
#
#     def plus(x):
#         x = x.replace('+', '').strip()
#         return x
#
#     df['Date Posted'] = df['Date Posted'].apply(posted)
#     df['Date Posted'] = df['Date Posted'].apply(day)
#     df['Date Posted'] = df['Date Posted'].apply(plus)
#
#     return df


# def sort_data(df):
#     def convert_to_integer(x):
#         try:
#             return int(x)
#         except ValueError:
#             return float('inf')
#
#     df['Date_num'] = df['Date Posted'].apply(lambda x: x[:2].strip())
#     df['Date_num2'] = df['Date_num'].apply(convert_to_integer)
#     df.sort_values(by=['Date_num2'], inplace=True)
#
#     df = df[['Link', 'Job Title', 'Company', 'Date Posted', 'Location']]
#     return df


def save_csv(df, job_position, job_location):
    # Define the path to save the file
    def get_fyp_jobs_data_path():
        # Replace with your desired directory path
        path = r'C:\My Drive\University\FYP\jobs data'
        return path

    # Create the full file path using job_position and job_location
    file_path = os.path.join(get_fyp_jobs_data_path(), '{}_{}.csv'.format(job_position, job_location))

    # Check if the file already exists
    if os.path.exists(file_path):
        # If file exists, append the data without writing the header again
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        # If the file doesn't exist, create it and write the data with the header
        df.to_csv(file_path, mode='w', index=False)

    return file_path


def generate_attachment_filename(job_title, job_location):
    filename = f"{job_title.replace(' ', '_')}_{job_location.replace(' ', '_')}.csv"
    return filename
