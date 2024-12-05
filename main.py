from dotenv import load_dotenv
from job_scraper_utils import *

load_dotenv()
pakistan = 'https://pk.indeed.com'
def main():
    #issues:
    # 1. are you a human? check
    # 2. something missing in results.
    driver = configure_webdriver()
    country = pakistan
    job_position = ''
    job_location = 'Punjab'
    date_posted = 1

    df = None
    try:
        full_url = search_jobs(driver, country, job_position, job_location, date_posted)
        # it makes files
        scrape_job_data(driver, country)
        df = read_job_pages()

        if df.shape[0] == 1:
            print("No results found. Something went wrong.")

    finally:
        try:
            print("hehe")
            save_csv(df, job_position, job_location)
            delete_job_pages_files()
        except Exception as e:
            print(f"Error saving file: {e}")
        finally:
            pass
            driver.quit()
            print("hehe")


if __name__ == "__main__":
    main()
