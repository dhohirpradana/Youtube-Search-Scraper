from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import urllib.parse
import datetime
import os
from selenium.webdriver.chrome.options import Options

# binary = FirefoxBinary(r'C:\Program Files\Mozilla Firefox\firefox.exe')

# options = webdriver.FirefoxOptions()
# options.add_argument("--headless")
# options.add_argument("--window-size=1920,1080")
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-extensions")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--disable-features=VizDisplayCompositor")
# options.add_argument("--disable-features=NetworkService")
# # , firefox_binary=binary

# driver = webdriver.Firefox(options=options)

def set_chrome_options() -> Options:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options

driver = webdriver.Chrome(options=set_chrome_options())
driver.delete_all_cookies()
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')


def handler(request, jsonify):
    body = request.get_json()

    if body is None:
        return jsonify({'message': 'No body provided'}), 400

    try:
        query = body['query']
        scroll = body['scroll']
    except Exception as e:
        return jsonify({'message': str(e) + " not provided"}), 400

    query_url = urllib.parse.quote(query)
    print('Query URL: ', query_url)
    now = datetime.datetime.now()

    try:
        driver.get(f"https://www.youtube.com/results?search_query={query_url}")

        scroll_height = driver.execute_script("return window.innerHeight")
        video_links = []
        video_titles = []
        video_views = []
        video_published_times = []

        res_data = []

        max_scroll = scroll
        file_name = f"{query}_scroll-{max_scroll}_{now.strftime('%Y%m%d_%H%M%S')}"

        scroll_num = 1
        # while True:
        while scroll_num <= max_scroll:
            print(f"Scrolling {scroll_num} of {max_scroll}")
            video_ids = driver.find_elements(
                By.XPATH, "//a[@id='video-title']")

            finish_video_ids = False
            for i, video_id in enumerate(video_ids):
                # skip playlist
                if "list" in video_id.get_attribute("href"):
                    print("playlist")
                    continue

                # skip channel
                if video_id.get_attribute("href").startswith("/@"):
                    print("channel")
                    continue

                video_links.append(video_id.get_attribute("href"))
                video_titles.append(video_id.get_attribute("title"))
                
                if i == len(video_ids) - 1:
                    finish_video_ids = True

            video_infos = driver.find_elements(
                By.XPATH, "//span[@class='inline-metadata-item style-scope ytd-video-meta-block']")

            finish_video_infos = False
            for i, video_info in enumerate(video_infos):
                if "views" in video_info.text or "ditonton" in video_info.text:
                    view_count = video_info.text
                    video_views.append(view_count)
                elif "ago" in video_info.text or "yang lalu" in video_info.text:
                    published_time = video_info.text
                    video_published_times.append(published_time)
                
                if i == len(video_infos) - 1:
                    finish_video_infos = True

            # print("video_links:", len(video_links))
            # print("video_titles:", len(video_titles))
            # print("video_views:", len(video_views))
            # print("video_published_times:", len(video_published_times))

            def write_to_file():
                if finish_video_ids and finish_video_infos:
                    with open(f"{BASE_DIR}/results/{file_name}.txt", "a", encoding="utf-8") as f:
                        for i, video_link in enumerate(video_links):
                            try:
                                v_title = video_titles[i]
                            except IndexError:
                                v_title = "-"

                            try:
                                v_views = video_views[i]
                            except IndexError:
                                v_views = "-"

                            try:
                                v_published_times = video_published_times[i]
                            except IndexError:
                                v_published_times = "-"

                            res_data.append({
                                "url": video_link,
                                "title": v_title,
                                "views": v_views,
                                "published": v_published_times
                            })

                            if i < len(video_links) - 1:
                                f.write(
                                    f"{video_link}¦¦{v_title}¦¦{v_views}¦¦{v_published_times}\n")
                            else:
                                f.write(
                                    f"{video_link}¦¦{v_title}¦¦{v_views}¦¦{v_published_times}")
                else:
                    print("Video ID or Video Info not finished")
                    write_to_file()
                    
            write_to_file()

            document_height_before = driver.execute_script(
                "return document.documentElement.scrollHeight")
            driver.execute_script(
                f"window.scrollTo(0, {document_height_before + scroll_height});")

            scroll_num += 1

            # delay before next scroll
            time.sleep(2)
            document_height_after = driver.execute_script(
                "return document.documentElement.scrollHeight")
            
            # end of scroll
            if document_height_after == document_height_before:
                break
            
    except Exception as e:
        print("Error: ", e)
        return jsonify({'message': str(e)}), 500

    return jsonify({'message': 'success', "filename": f"{file_name}.txt", "results": res_data}), 200
