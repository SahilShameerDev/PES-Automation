from appium import webdriver
from appium.options.common import AppiumOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
import time
import cv2
import os
from PIL import Image
import pytesseract
from skimage.metrics import structural_similarity as ssim
import json
from playsound import playsound
import subprocess, sys
import numpy as np


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#...........................................
# Global Variables

#Tap
LANGUAGE_EN_COORDS = (470, 400)  
OK_COORDS = (2000,990)
JAPAN_COORDS = (508,294)
CONFIRM_COORDS = (1500,650)
MINOR_COORDS = (1300,740)
TERMS_SELECT_COORDS = (1248,943)
TERMS_AGREE_COORDS = (509,813)
TERMS_ACCEPT_COORDS = (1544,914)
OPTION_COORDS = (1240,390)
OPTION_ACCEPT = (1300,940)
DOWNLOAD_COORDS = (1440,700)
WELCOME_COORDS = (1800,820)

ENTER_COORDS = (1150,810)
TEAM_COORDS = (1500,810)

REWARD_SECTION = (1870,56)
REWARD = (1257,987)
RBACK = (300,980)

CONTRACT_COORDS = (1160,890)
SPECIAL_PLAYER_COORDS = (650,650)

SPIN_COORDS = (900, 600)
SPIN = (1180,640)

BACK_CONFIRM = (2300, 995)


#Swipe
REGION_SWIPE = (1300,860,1300,600, 400)
LANG_SWIPE = (1300,800,1300,710, 1500)
SPIN_SWIPE = (632,493,102,493, 500)
SPIN_SELECT_COORDS = (1920,500)

# ..........................................
# Initializing Drivers
def create_driver():
    caps = {
        "platformName": "Android",
        "deviceName": "AndroidDevice",
        "automationName": "UiAutomator2",
        "appium:appPackage": "jp.konami.pesam",
        "appium:appActivity": "com.epicgames.ue4.GameActivity",
        "newCommandTimeout": 1200,
        "noReset": True
    }
    options = AppiumOptions()
    options.load_capabilities(caps)
    return webdriver.Remote("http://127.0.0.1:4723", options=options)

# ..........................................
# Force stop and clear data
def reset_app(package="jp.konami.pesam"):
    os.system(f"adb shell am force-stop {package}")
    os.system(f"adb shell pm clear {package}")
    print(f"[+] App force-stopped and data cleared")




# ..........................................
# Tapping function at a coordinate
def tap_at(driver, x, y):
    actions = ActionChains(driver)
    touch = PointerInput(interaction.POINTER_TOUCH, "touch")
    actions.w3c_actions = ActionBuilder(driver, mouse=touch)

    actions.w3c_actions.pointer_action.move_to_location(x, y)
    actions.w3c_actions.pointer_action.pointer_down()
    actions.w3c_actions.pointer_action.pause(0.1)
    actions.w3c_actions.pointer_action.pointer_up()

    actions.perform()


# ..........................................
# Scrolling Functions
def scroll(driver,COORDS):
    print("Scrolled")
    st_x,st_y,e_x,e_y, dur=COORDS
    # swipe from bottom → top (adjust based on your screen)
    driver.swipe(
        start_x=st_x, start_y=st_y,   # bottom center
        end_x=e_x,   end_y=e_y,      # top center
        duration=dur
    )
    time.sleep(1)



# ..........................................
# General Tapping function
def tap(driver,COORDS,msg="Message"):
    x,y=COORDS
    tap_at(driver,x,y)
    print(f'Tapped at {msg}({x},{y})')
    return True
    



# ..........................................
# Allowing permissions
def allow_permission_if_shown(driver):
    time.sleep(2)
    allow_ids = [
        "com.android.permissioncontroller:id/permission_allow_button",
        "com.android.packageinstaller:id/permission_allow_button"
    ]

    for allow_id in allow_ids:
        try:
            btn = driver.find_element("id", allow_id)
            btn.click()
            print("[+] Permission allowed")
            return True
        except:
            pass

    print("[-] No permission popup found")
    return False

def is_session_alive(driver):
    try:
        driver.get_window_size()
        return True
    except:
        return False


def crop_player_names(img_path):
    img = cv2.imread(img_path)

    # ---- NEW COORDINATES BASED ON REAL IMAGE ----
    # Move up: y1 = 0.35 h, y2 = 0.47 h

    # Player 1 (Left card)
    p1_x1 = int(455)
    p1_y1 = int(20)
    p1_x2 = int(1150)
    p1_y2 = int(142)

    player1 = img[p1_y1:p1_y2, p1_x1:p1_x2]
    output_path = os.path.join("images", "player1_name.png")
    cv2.imwrite(output_path, player1)

    

    print("[+] Cropped player name regions (corrected).")
    return output_path

#...........................................
# For finding region text 
def crop_region_text(img_path):
    img = cv2.imread(img_path)
    if img is None:
        print("[ERROR] screenshot not found")
        return None

    # Given coordinates
    x1, y1, x2, y2 = 216, 240, 1117, 330

    crop = img[y1:y2, x1:x2]
    output_path = os.path.join("images", "region_crop.png")
    cv2.imwrite(output_path, crop)
    return output_path

def read_region_name(crop_path):
    try:
        if not os.path.exists(crop_path):
            print(f"[ERROR] Crop file does not exist: {crop_path}")
            return ""

        # Load with OpenCV for preprocessing
        img = cv2.imread(crop_path)
        if img is None:
            print(f"[ERROR] Failed to read image: {crop_path}")
            return ""

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Upscale to help OCR
        gray = cv2.resize(
            gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
        )

        # Binarize (clean text)
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Debug: save what OCR actually sees
        debug_path = os.path.join("images", "region_ocr_debug.png")
        cv2.imwrite(debug_path, thresh)

        # Make sure Tesseract path is correct on Windows (adjust if needed)
        # import pytesseract
        # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

        config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
        text = pytesseract.image_to_string(thresh, config=config)

        cleaned = text.strip().lower()
        print(f"[DEBUG] OCR raw: {repr(text)}, cleaned: {cleaned}")
        return cleaned

    except Exception as e:
        print(f"[ERROR] OCR failed on region text: {e}")
        return ""



def find_and_select_region(driver, target_region, scroll_coords, tap_coords):
    target_region = target_region.lower()

    print(f"[*] Searching for region: {target_region}")

    for i in range(25):  # max 25 scrolls
        # take screenshot
        screenshot_path = os.path.join("images", "current_screen_lang.png")
        driver.save_screenshot(screenshot_path)

        # crop region
        crop_path = crop_region_text(screenshot_path)
        if crop_path is None:
            print("[ERROR] Could not crop region text.")
            return False

        # OCR read
        text = read_region_name(crop_path)
        print(f"Detected region: {text}")

        # check match
        if target_region in text:
            print(f"🎉 Region '{target_region}' FOUND!")
            tap(driver, tap_coords, msg=f"Select {target_region}")
            return True

        # if not matched → scroll
        scroll(driver, scroll_coords)

    print("❌ Region not found after full scroll range.")
    return False
#.................................................................


def read_player_name(img_path):
    # Load image
    img = cv2.imread(img_path)

    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Upscale 2× for better OCR
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # 3. Reduce noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # 4. Use adaptive thresholding for white text
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        31, 10
    )

    # 5. Morphology to thicken text
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)

    # DEBUG — Save what Tesseract sees
    debug_path = os.path.join("images", "player_ocr_debug.png")
    cv2.imwrite(debug_path, thresh)

    # 6. OCR
    config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
    text = pytesseract.image_to_string(thresh, config=config)

    cleaned = text.strip().lower()
    return cleaned




def load_wanted_players(json_path="players_needed.json"):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            return [name.lower().replace(" ", "") for name in data.get("players", [])]
    except Exception as e:
        print(f"[ERROR] Failed to load wanted players: {e}")
        return []
    
def load_event_names(json_path="event_config.json"):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            events = data.get("events", [])
            return [e.lower().replace(" ", "") for e in events]
    except Exception as e:
        print(f"[ERROR] Failed to load event names: {e}")
        return []
    
def load_region_name(json_path="region_config.json"):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            region = data.get("region", "")
            return region.lower().replace(" ", "")
    except Exception as e:
        print(f"[ERROR] Failed to load event names: {e}")
        return []
    


def go_back(driver):
    tap(driver, BACK_CONFIRM, msg="Back from event")
    time.sleep(2)


# ..........................................
# Check for wanted players
def check_players(driver):
    wanted_names = load_wanted_players()   # <-- reads from JSON
    tap(driver, (616, 291), msg="Capture Screen for Player Names")
    time.sleep(5)
    screenshot_path = os.path.join("images", "player_screen.png")
    driver.save_screenshot(screenshot_path)
    p1_crop = crop_player_names(screenshot_path)
    p1_name = read_player_name(p1_crop)
    print(f"[DEBUG] Player 1 detected name: {p1_name}")
    if p1_name in wanted_names:
        return True
    tap(driver, (2133, 96), msg="Closed Player screen")
    time.sleep(2)
    
    tap(driver, (964, 291), msg="Capture Screen for Player Names")
    time.sleep(5)
    screenshot_path = os.path.join("images", "player_screen.png")
    driver.save_screenshot(screenshot_path)
    p1_crop = crop_player_names(screenshot_path)
    p1_name = read_player_name(p1_crop)
    print(f"[DEBUG] Player 2 detected name: {p1_name}")
    if p1_name in wanted_names:
        return True
    
    tap(driver, (2133, 96), msg="Closed Player screen")
    return False
    

    
    
def ring_phone_adb():
    print("[+] Ringing phone using ADB...")
    os.system("aadb shell am start -a android.intent.action.VIEW -t audio/* -d content://settings/system/ringtone")

def send_appium_notification(driver):
    driver.execute_script("mobile: broadcast", {
        "intent": "android.intent.action.NOTIFY",
        "extras": {"message": "Special Player Found!"}
    })

def is_goal_screen(current_img, goal_template, threshold=0.70):
    img1 = cv2.imread(current_img, 0)
    img2 = cv2.imread(goal_template, 0)

    # resize template to match screenshot resolution
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    score, diff = ssim(img1, img2, full=True)
    print("SSIM Score:", score)

    return score >= threshold

def wait_for_goal(driver):
    print("[*] Waiting for GOAL screen...")

    for i in range(60):  # 60 checks ~ 3-5 min max
        screenshot_path = os.path.join("images", "current_screen.png")
        driver.save_screenshot(screenshot_path)

        if is_goal_screen(screenshot_path, "./targets/goal_screen.png"):
            print("GOAL detected!")
            return True

        time.sleep(5)  # check again every 5 seconds

    print("GOAL not detected within timeout.")
    return False


def alert_player_found():
    print("[+] Player found! Triggering alerts...")

    # 1. Notification
    os.system("adb shell cmd notification post -S bigtext -t 'PLAYER FOUND!' 'auto.bot' 'A wanted player is detected!'")

    # 2. Vibrate for 5 seconds
    os.system("adb shell cmd vibrator vibrate 5000")

    # 3. Play sound
    # Play alert.mp3 on the PC (tries playsound, then OS fallbacks)
    try:
        playsound(os.path.abspath("alert.mp3"))
    except Exception as e:
        try:
            path = os.path.abspath("alert.mp3")
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["afplay", path], check=False)
            else:
                # Try common linux players
                for player in (["paplay"], ["aplay"], ["mpg123"], ["mpv", "--no-video"]):
                    try:
                        subprocess.run(player + [path], check=True)
                        break
                    except Exception:
                        continue
        except Exception as e2:
            print(f"[ERROR] Unable to play alert.mp3: {e2}")
            
def wait_until_home(driver, template_path="./targets/home_screen.jpg", threshold=0.70):
    print("[*] Trying to reach HOME screen...")

    template = cv2.imread(template_path, 0)
    if template is None:
        print("[ERROR] Home template image missing:", template_path)
        return False

    for i in range(15):  # Press BACK max 15 times
        # Take screenshot
        screenshot_path = os.path.join("images", "screen_home_check.png")
        driver.save_screenshot(screenshot_path)

        screen = cv2.imread(screenshot_path, 0)
        if screen is None:
            print("[ERROR] Failed to read screenshot.")
            return False

        # Resize template to match screenshot resolution
        tpl_resized = cv2.resize(template, (screen.shape[1], screen.shape[0]))

        # SSIM comparison
        score, _ = ssim(screen, tpl_resized, full=True)

        print(f"[DEBUG] HOME SSIM Score: {score}")

        if score >= threshold:
            print("🏠 HOME SCREEN DETECTED!")
            return True

        print("❌ Not home yet → pressing BACK")
        driver.back()
        time.sleep(2)

    print("⚠ Could not reach home within limit.")
    return False


def crop_spin_section(img_path):
    img = cv2.imread(img_path)
    if img is None:
        print("[ERROR] Could not read screenshot")
        return None

    H, W = img.shape[:2]

    # Percentages (based on your device)
    x1_p, y1_p = 0.1875, 0.5409
    x2_p, y2_p = 0.6125, 0.6090

    # Convert to pixel values dynamically
    x1 = int(W * x1_p)
    y1 = int(H * y1_p)
    x2 = int(W * x2_p)
    y2 = int(H * y2_p)

    crop = img[y1:y2, x1:x2]
    output_path = os.path.join("images", "spin_section_crop.png")
    cv2.imwrite(output_path, crop)
    return output_path


def read_spin_section(crop_path):
    img = cv2.imread(crop_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2)
    gray = cv2.GaussianBlur(gray, (3,3), 0)

    _, thresh = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
    text = pytesseract.image_to_string(thresh, config=config)

    return text.strip().lower()


def find_spin_section(driver, event_text):
    print(f"[*] Searching for spin section: {event_text}")

    for i in range(10):
        screenshot_path = os.path.join("images", "spin_full.png")
        driver.save_screenshot(screenshot_path)

        crop_path = crop_spin_section(screenshot_path)
        text = read_spin_section(crop_path)

        print(f"[DEBUG] OCR spin text: {text}")

        if event_text in text:
            print("🎯 Event matched!")
            return True

        # Horizontal scroll
        driver.swipe(
            start_x=400, start_y=600,
            end_x=50,  end_y=600,
            duration=600
        )
        time.sleep(1)

    return False


# ..........................................
# Main Function
def main():
    if not os.path.exists("images"):
        os.mkdir("images")

    while True:
        driver = None
        try:
            # Opening The App
            print("\n[+] Starting new session...")
            driver = create_driver()
            time.sleep(5)
            
            # Allowing Permissions
            allow_permission_if_shown(driver=driver)
            time.sleep(15)
            
            # Choosing Language
            tap(driver=driver, COORDS=LANGUAGE_EN_COORDS, msg="Language")
            
            #Clicking Ok
            tap(driver=driver, COORDS=OK_COORDS, msg="Ok")
            time.sleep(20)
            
            # Selecting region
            find_and_select_region(driver, target_region=load_region_name("region_config.json"), scroll_coords=LANG_SWIPE, tap_coords=JAPAN_COORDS)
            time.sleep(2)
            #Clicking Ok
            tap(driver=driver, COORDS=OK_COORDS,msg="Ok")
            time.sleep(3)
            
            tap(driver=driver, COORDS=CONFIRM_COORDS,msg="Confirm")
            time.sleep(16)
            
            tap(driver=driver, COORDS=MINOR_COORDS, msg="Minor Accept")
            tap(driver=driver,COORDS=TERMS_SELECT_COORDS, msg="Privacy menu select")
            time.sleep(1)
            tap(driver=driver,COORDS=TERMS_AGREE_COORDS, msg="1st terms agree")
            tap(driver=driver,COORDS=TERMS_ACCEPT_COORDS,msg="1st terms accept")
            time.sleep(2)
            tap(driver=driver,COORDS=TERMS_AGREE_COORDS, msg="2nd terms agree")
            tap(driver=driver,COORDS=TERMS_ACCEPT_COORDS, msg="2nd terms accept")
            time.sleep(10)
            tap(driver=driver,COORDS=OPTION_COORDS, msg="Preference Selected 1")
            tap(driver=driver,COORDS=OPTION_ACCEPT,msg="Preference Accepted 1")
            time.sleep(1)
            tap(driver=driver,COORDS=OPTION_COORDS, msg="Preference Selected 2")
            tap(driver=driver,COORDS=OPTION_ACCEPT, msg="Preference Accepted 2")
            time.sleep(1)
            tap(driver=driver,COORDS=OPTION_COORDS, msg="Preference Selected 3")
            tap(driver=driver,COORDS=OPTION_ACCEPT, msg="Preference Accepted 3")
            time.sleep(1)
            tap(driver=driver,COORDS=OPTION_ACCEPT, msg="Username Selected")
            time.sleep(20)
            tap(driver=driver,COORDS=DOWNLOAD_COORDS, msg="Download Started")
            if(not wait_for_goal(driver=driver)):
                reset_app()
                print("Terminated App....")     
            # GOAL
            scroll(driver=driver,COORDS=REGION_SWIPE)
            time.sleep(30)
            tap(driver=driver,COORDS=WELCOME_COORDS, msg=" Welcome page button clicked")
            time.sleep(5)
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=TEAM_COORDS, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Clikced OK")
            time.sleep(2)
            
            wait_until_home(driver)

            time.sleep(3)
            
            #REWARDS
            tap(driver=driver,COORDS=REWARD_SECTION, msg="Clikced Reward Section")
            time.sleep(2)
            tap(driver=driver,COORDS=REWARD, msg="Clikced Rewards")
            time.sleep(5)
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Accepted Rewards")
            time.sleep(2)
            tap(driver=driver,COORDS=RBACK, msg="Back to Home Screen")
            time.sleep(5)
            
            #CONTRACT SPIN
            tap(driver=driver,COORDS=CONTRACT_COORDS, msg="Clikced Contract")
            time.sleep(2)
            tap(driver=driver,COORDS=SPECIAL_PLAYER_COORDS, msg="Clikced Special Player" )
            time.sleep(5)
            event_list = load_event_names()
            print(f"Loaded events: {event_list}")

            player_found = False

            for event in event_list:
                print(f"\n===== Checking event: {event} =====")

                # 1. Find event section
                if not find_spin_section(driver, event):
                    print("❌ Could not find this event, skipping...")
                    continue

                # 2. Enter event
                tap(driver, SPIN_SELECT_COORDS, msg="Enter event")
                time.sleep(2)

                # 3. Spin
                tap(driver, SPIN_COORDS, msg="Clicked Spin")
                time.sleep(3)
                tap(driver, SPIN, msg="Spin Complete")
                time.sleep(3)
                tap(driver, SPIN_COORDS)  # show results
                time.sleep(30)

                # 4. Check players
                if check_players(driver):
                    print("🎉 Special Player Found! Stopping now.")
                    alert_player_found()
                    send_appium_notification(driver)
                    player_found = True
                    break

                print("No player in this event → going back.")
                go_back(driver)
                time.sleep(2)
            
            if not player_found:
                print("No player found in ANY event. Restarting app.")
                reset_app()
                print("App Restarted.")


                         
            
            
        except Exception as e:
            print(f"[ERROR] {e}")
            reset_app()
            print("Terminated App....")

        finally:
            if driver:
                driver.quit()
            time.sleep(2)
            
            

if __name__ == "__main__":
    main()

