from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from pathlib import Path
import json
from tqdm import tqdm

##### Constants #####
# Instagram login credentials
USERNAME = "USERNAME"  # Replace with your username
PASSWORD = "PASSWORD"  # Replace with your password
N_SCROLLS = 20  # Number of scrolls to load more comments
USER_IDS_FILE = Path(__file__).parent / "users.jsonl"
POST_IDS_JSON = Path(__file__).parent / "post_ids.json"


def read_user_ids():
    file_path = USER_IDS_FILE.as_posix()
    with open(file_path, "r") as file:
        return [json.loads(line) for line in file]


user_ids = read_user_ids()

# Initialize WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Start the browser maximized
service = Service()  # Or use ChromeDriverManager for automatic management
driver = webdriver.Chrome(service=service, options=options)

# Open Instagram
driver.get("https://www.instagram.com")

# Wait for the page to load
time.sleep(1)

# Locate the username and password fields and the login button
username_field = driver.find_element(
    By.XPATH, '//*[@id="loginForm"]/div[1]/div[1]/div/label/input'
)
password_field = driver.find_element(
    By.XPATH, '//*[@id="loginForm"]/div[1]/div[2]/div/label/input'
)
login_button = driver.find_element(By.XPATH, "//*[@id='loginForm']/div[1]/div[3]")

# Enter your credentials
username_field.send_keys(USERNAME)  # Replace with your username
password_field.send_keys(PASSWORD)  # Replace with your password

# Click the login button
login_button.click()

# Find button with text "Not Now" and click it
time.sleep(5)
try:
    save_info_button = driver.find_element(By.XPATH, "//button[text()='Save info']")
    save_info_button.click()
except Exception as e:
    print(f"Save info button not found or could not be clicked: {e}")

# Open the specific Instagram profile
user_url_template = (
    "https://www.instagram.com/{USER_ID}"  # Replace with the actual post link
)


def get_posts(profile_url):
    time.sleep(3)
    driver.get(profile_url)
    time.sleep(2)

    # Locate the scrollable profile container (using the provided XPath)
    try:
        scrollable_element = driver.find_element(
            By.XPATH,
            "/html",
        )
    except Exception as e:
        print(f"An error occurred while locating the scrollable element: {e}")
        scrollable_element = None

    if scrollable_element:
        # Scroll down within the container to load more comments
        for _ in range(N_SCROLLS):  # Adjust the number of scrolls as needed
            try:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight",
                    scrollable_element,
                )
                time.sleep(2)  # Wait for new content to load after scrolling
            except Exception as e:
                print(f"An error occurred while scrolling: {e}")
                break
    else:
        print("Scrollable element not found. Cannot perform scrolling.")

    posts = []

    # After scrolling, extract the posts
    # Loop through posts dynamically
    for i in range(N_SCROLLS * 10):  # Adjust the range as needed
        row = i // 3 + 1
        col = i % 3 + 1
        try:
            post_xpath = f"/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/div[2]/div/div/div[{row}]/div[{col}]/a"
            post_elements = driver.find_elements(By.XPATH, post_xpath)
            if post_elements is None:
                break
            for post_element in post_elements:
                try:
                    url = post_element.get_attribute("href")
                    print(url)
                    # split by "/" and get the last element
                    post_id = url.split("/")[-2]
                    print(post_id)

                    posts.append(post_id)

                except Exception as e:
                    print(f"⚠️ Skipping an unreadable comment: {e}")

        except Exception as e:
            print(f"⚠️ Comment {i} failed to be extracted: {e}")

    return posts


for i, user_id in tqdm(
    enumerate(user_ids), desc="Processing posts", total=len(user_ids)
):
    profile_url = user_url_template.format(USER_ID=user_id)
    posts = get_posts(profile_url)
    # Save posts to a file
    mode = "a"
    with open(POST_IDS_JSON, mode) as file:
        file.write("\n".join(posts))
        file.write("\n")
