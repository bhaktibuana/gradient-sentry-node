from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException, NoSuchDriverException

import os
import requests
import hashlib
import time
from flask import Flask

# Load .env file from root directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

extensionId = 'caacbgbklghmpodbdafajbgdnegacfmo' # Gradient Sentry Node ext_id
CRX_URL = "https://clients2.google.com/service/update2/crx?response=redirect&prodversion=98.0.4758.102&acceptformat=crx2,crx3&x=id%3D~~~~%26uc&nacl_arch=x86-64"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"

try:
    EMAIL = os.environ['GRADIENT_EMAIL']
    PASSW = os.environ['GRADIENT_PASS']
except:
    EMAIL = ''
    PASSW = ''

try:
    ALLOW_DEBUG = os.environ['ALLOW_DEBUG']
    if ALLOW_DEBUG == 'True':
        ALLOW_DEBUG = True
    else:
        ALLOW_DEBUG = False
except:
    ALLOW_DEBUG = False

if EMAIL == '' or PASSW == '':
    print('Please set GRADIENT_EMAIL and GRADIENT_PASS env variables')
    exit()

if ALLOW_DEBUG == True:
    print('Debugging is enabled! This will generate a screenshot and console logs on error!')


# Download ext function
def download_extension(extension_id):
    url = CRX_URL.replace("~~~~", extension_id)
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, stream=True, headers=headers)
    with open("gradient.crx", "wb") as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
    if ALLOW_DEBUG == True:
        #generate md5 of file
        md5 = hashlib.md5(open('gradient.crx', 'rb').read()).hexdigest()
        print('Extension MD5: ' + md5)


# Generate error report function
def generate_error_report(driver):
    if not ALLOW_DEBUG:
        return
    
    # Take screenshot
    screenshot_path = 'error.png'
    driver.save_screenshot(screenshot_path)

    # Grab console logs
    log_path = 'error.log'
    logs = driver.get_log('browser')
    with open(log_path, 'w') as f:
        for log in logs:
            f.write(str(log) + '\n')

    url = 'https://cloud.bhaktibuana.com/api/uploader'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjZmZDFlMGU1Y2Y0MGYwZjFhN2M3ZjIwIiwibmFtZSI6ImFpcmRyb3AiLCJpYXQiOjE3MzE2NDIyNjd9.Z7sCVXGgMyttbF69wxLvBHpkvCS5Im8XPB2Mzq56zhs'

    files = {
        'file': (screenshot_path, open(screenshot_path, 'rb'), 'image/png')
    }
    data = {'token': token}

    response = requests.post(url, files=files, data=data)

    if response.status_code == 201:
        try:
            res_data = response.json()
            file_url = res_data.get('data', {}).get('url')
            if file_url:
                print('Uploaded File URL:', file_url)
                return file_url
            else:
                print('Upload response does not contain a URL:', res_data)
        except requests.exceptions.JSONDecodeError:
            print('Failed to parse JSON response:', response.text)
    else:
        print('Upload failed with status:', response.status_code, response.text)

    return None


# start to install extention
print('Downloading extension...')
download_extension(extensionId)
print('Downloaded! Installing extension and driver manager...')

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--no-sandbox')

options.add_extension('gradient.crx')

print('Installed! Starting...')
try:
    driver = webdriver.Chrome(options=options)
except (WebDriverException, NoSuchDriverException) as e:
    print('Could not start with Manager! Trying to default to manual path...')
    try:
        driver_path = "/usr/bin/chromedriver"
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
    except (WebDriverException, NoSuchDriverException) as e:
        print('Could not start with manual path! Exiting...')
        exit()

# Start to login
print('Started! Logging in...')
driver.get('https://app.gradient.network/')

sleep = 0
while True:
    try:
        driver.find_element('xpath', '//*[@placeholder="Enter Email"]')
        driver.find_element('xpath', '//*[@placeholder="Enter Password"]')
        driver.find_element('xpath', '//button[contains(text(), "Log In")]')
        break
    except:
        time.sleep(1)
        print('Loading login form...')
        sleep += 1
        if sleep > 15:
            print('Could not load login form! Exiting...')
            generate_error_report(driver)
            driver.quit()
            exit()

time.sleep(2)

user = driver.find_element('xpath', '//*[@placeholder="Enter Email"]')
passw = driver.find_element('xpath', '//*[@placeholder="Enter Password"]')
submit = driver.find_element('xpath', '//button[contains(text(), "Log In")]')

user.send_keys(EMAIL)
passw.send_keys(PASSW)
submit.click()

sleep = 0
while True:
    try:
        e = driver.find_element('xpath', '//*[contains(text(), "Referred")]')
        break
    except:
        time.sleep(1)
        print('Logging in...')
        sleep += 1
        if sleep > 10:
            print('Could not login! Double Check your username and password! Exiting...')
            generate_error_report(driver)
            driver.quit()
            exit()

print('Logged in! Waiting for connection...')
driver.get('chrome-extension://'+extensionId+'/popup.html')
sleep = 0
while True:
    try:
        driver.find_element('xpath', '//*[contains(text(), "Today\'s Taps")]')
        break
    except:
        time.sleep(1)
        print('Loading connection...')
        sleep += 1
        if sleep > 30:
            print('Could not load connection! Exiting...')
            generate_error_report(driver)
            driver.quit()
            exit()

sleep = 0
while True:
    try:
        close = driver.find_element('xpath', '//button[contains(text(), "Close")]')
        close.click()
        break
    except:
        time.sleep(1)
        print('Closing Warm Reminder...')
        sleep += 1
        if sleep > 10:
            print('Skip closing Warm Reminder...')
            break

sleep = 0
while True:
    try:
        onboarding = driver.find_element('xpath', '//button[contains(text(), "I got it")]')
        onboarding.click()
        break
    except:
        time.sleep(1)
        print('Closing On Boarding...')
        sleep += 1
        if sleep > 10:
            print('Skip closing On Boarding...')
            break

print('Connected! Starting API...')



# #flask api
app = Flask(__name__)

@app.route('/')
def get():
    url = ''
    message = ''
    try:
       url = generate_error_report(driver)
       message = 'Sentry Nodes Report'
    except:
        print('Could not get Sentry Nodes Report')
        message = 'Could not get Sentry Nodes Report'

    return {'message': message, 'url': url}

@app.route('/close-onboarding')
def closeOnboarding():
    url = ''
    message = ''
    try:
        onboarding = driver.find_element('xpath', '//button[contains(text(), "I got it")]')
        onboarding.click()
        message = 'Success close On Boarding'
    except Exception as e:
        message = 'Failed close On Boarding'
        
    url = generate_error_report(driver)
    return {'message': message, 'url': url}

@app.route('/close-warning')
def closeWarning():
    url = ''
    message = ''
    try:
        close = driver.find_element('xpath', '//button[contains(text(), "Close")]')
        close.click()
        message = 'Success close Warm Reminder'
    except Exception as e:
        message = 'Failed close Warm Reminder'
        
    url = generate_error_report(driver)
    return {'message': message, 'url': url}

app.run(host='0.0.0.0',port=4010, debug=False)
driver.quit()
