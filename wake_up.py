import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 👉 REPLACE THIS WITH YOUR STREAMLIT APP URL
APP_URL = "https://subjectrisk-ngankeu-takou-daniel-wilfried-24g2678.streamlit.app/"

def wake_up_app():
    print(f"Visiting {APP_URL}...")
    
    # Set up a "headless" hidden browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(APP_URL)
        time.sleep(5) # Give the page a moment to load
        
        # Look for the sleep button and click it if it exists
        try:
            wake_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes, get this app back up')]"))
            )
            print("App is asleep! Clicking the wake up button...")
            wake_button.click()
            time.sleep(5)
            print("App successfully woken up!")
        except:
            print("No wake up button found. The app is already awake! ✅")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    wake_up_app()
