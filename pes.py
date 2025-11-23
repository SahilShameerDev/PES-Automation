from appium import webdriver
from appium.options.common import AppiumOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
import time
import cv2
import numpy as np
import os
from PIL import Image
import pytesseract
from skimage.metrics import structural_similarity as ssim


#...........................................
# Global Variables

#Tap
LANGUAGE_EN_COORDS = (470, 400)  
OK_COORDS = (2000,990)
JAPAN_COORDS = (710,880)
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

SPIN_COORDS = (1680, 980)
SPIN = (1180,640)

#Swipe
REGION_SWIPE = (1300,860,1300,600)
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
# Scrolling Function
def scroll(driver,COORDS):
    print("Scrolled")
    st_x,st_y,e_x,e_y=COORDS
    # swipe from bottom → top (adjust based on your screen)
    driver.swipe(
        start_x=st_x, start_y=st_y,   # bottom center
        end_x=e_x,   end_y=e_y,      # top center
        duration=400
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
    h, w, _ = img.shape

    # ---- CROP PLAYER 1 NAME (LEFT CARD) ----
    p1_x1 = int(w * 0.12)
    p1_y1 = int(h * 0.43)
    p1_x2 = int(w * 0.35)
    p1_y2 = int(h * 0.55)

    player1 = img[p1_y1:p1_y2, p1_x1:p1_x2]
    cv2.imwrite("player1_name.png", player1)

    # ---- CROP PLAYER 2 NAME (RIGHT CARD) ----
    p2_x1 = int(w * 0.38)
    p2_y1 = int(h * 0.43)
    p2_x2 = int(w * 0.60)
    p2_y2 = int(h * 0.55)

    player2 = img[p2_y1:p2_y2, p2_x1:p2_x2]
    cv2.imwrite("player2_name.png", player2)

    print("[+] Cropped both player name regions.")
    return "player1_name.png", "player2_name.png"

import pytesseract
from PIL import Image

def read_player_name(img_path):
    img = Image.open(img_path)

    config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
    text = pytesseract.image_to_string(img, config=config)

    cleaned = text.strip().lower()
    return cleaned

import json

def load_wanted_players(json_path="players_needed.json"):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            return [name.lower() for name in data.get("players", [])]
    except Exception as e:
        print(f"[ERROR] Failed to load wanted players: {e}")
        return []

def check_players(driver):
    wanted_names = load_wanted_players()   # <-- reads from JSON

    print("[*] Taking screenshot...")
    driver.save_screenshot("current_screen.png")

    p1_img, p2_img = crop_player_names("current_screen.png")

    print("[*] Running OCR...")
    name1 = read_player_name(p1_img)
    name2 = read_player_name(p2_img)

    print("Detected P1:", name1)
    print("Detected P2:", name2)

    for w in wanted_names:
        if w in name1 or w in name2:
            return True

    return False

def ring_phone_adb():
    print("[+] Ringing phone using ADB...")
    os.system("adb shell cmd notification post -S bigtext -t 'Player Found!' 'auto.bot.alert' 'Special player detected!'")
    os.system("adb shell media volume --show --stream 3 --set 15")  # set ring volume to max
    os.system("adb shell am start -a android.intent.action.RINGTONE")

def send_appium_notification(driver):
    driver.execute_script("mobile: broadcast", {
        "intent": "android.intent.action.NOTIFY",
        "extras": {"message": "Special Player Found!"}
    })

def is_goal_screen(current_img, goal_template, threshold=0.80):
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
        driver.save_screenshot("current_screen.png")

        if is_goal_screen("current_screen.png", "./targets/goal_screen.png"):
            print("GOAL detected!")
            return True

        time.sleep(5)  # check again every 5 seconds

    print("GOAL not detected within timeout.")
    return False

# ..........................................
# Main Function
def main():
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
            
            #Selecting region
            scroll(driver=driver,COORDS=REGION_SWIPE)
            tap(driver=driver,COORDS=JAPAN_COORDS, msg="Japan")
            
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
            if(not is_goal_screen):
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
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=OPTION_ACCEPT, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=OPTION_ACCEPT, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Clikced OK")
            time.sleep(2)
            tap(driver=driver,COORDS=ENTER_COORDS, msg="Clikced OK")
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
            tap(driver=driver,COORDS=SPIN_SELECT_COORDS, msg="Click Spin section")
            time.sleep(2)
            tap(driver=driver,COORDS=SPIN_COORDS, msg = "Clicked Spin")
            time.sleep(3)
            tap(driver=driver,COORDS=SPIN, msg= "Spin Complete" )
            time.sleep(3)
            tap(driver=driver,COORDS=SPIN_COORDS)
            time.sleep(30)
            
            #Checking if we got the right players
            if(check_players(driver=driver)):
                print("🎉 Special player found!")
                ring_phone_adb()
                send_appium_notification(driver)
                break
            else:
                print("Player Not Found")
                ring_phone_adb()
                reset_app()
                print("Terminated App....")                  
            
            
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

