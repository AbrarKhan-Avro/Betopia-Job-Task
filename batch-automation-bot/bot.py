from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import base64

from recognize_image import recognize_captcha

FORM_URL = "https://form.jotform.com/260231667243453"


class FormBot:
    def __init__(self, log_callback=None):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 30)
        self.log = log_callback or print

        # Captcha management
        self.captcha_dir = "captcha"
        self.captcha_path = os.path.join(self.captcha_dir, "current_captcha.png")
        os.makedirs(self.captcha_dir, exist_ok=True)

        self.last_captcha_src = None

    # =========================
    # FORM LOAD
    # =========================
    def open_form(self):
        self.driver.get(FORM_URL)
        time.sleep(2)
        self.capture_or_update_captcha(force=True)

    # =========================
    # CAPTCHA HANDLER
    # =========================
    def capture_or_update_captcha(self, force=False):
        try:
            captcha_img = self.driver.find_element(By.CLASS_NAME, "form-captcha-image")
            src = captcha_img.get_attribute("src")

            if not src or not src.startswith("data:image"):
                return

            if not force and src == self.last_captcha_src:
                return

            base64_data = src.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_data)

            if os.path.exists(self.captcha_path):
                os.remove(self.captcha_path)

            with open(self.captcha_path, "wb") as f:
                f.write(image_bytes)

            self.last_captcha_src = src
            self.log("🖼 Captcha updated: captcha/current_captcha.png")

        except Exception as e:
            self.log(f"⚠️ Captcha capture failed: {e}")

    # =========================
    # FORM FILLING
    # =========================
    def fill_form(self, row):
        self.wait.until(EC.presence_of_element_located((By.ID, "first_11"))).send_keys(row["FirstName"])
        self.driver.find_element(By.ID, "last_11").send_keys(row["LastName"])

        phone = str(row["Phone"])
        self.driver.find_element(By.ID, "input_13_area").send_keys(phone[:3])
        self.driver.find_element(By.ID, "input_13_phone").send_keys(phone[3:])

        self.driver.find_element(By.ID, "input_7").send_keys(row["Email"])

        Select(self.driver.find_element(By.ID, "input_15")).select_by_visible_text(row["ContactMethod"])
        Select(self.driver.find_element(By.ID, "input_17")).select_by_visible_text(row["HowFound"])

        self.driver.find_element(By.ID, "input_3").send_keys(row["Reason"])

        checkbox = self.driver.find_element(By.ID, "input_20_0")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
        time.sleep(0.5)
        self.driver.execute_script("arguments[0].click();", checkbox)

    # =========================
    # CAPTCHA SOLVE + SUBMIT
    # =========================
    def solve_and_submit_captcha(self):
        captcha_text = recognize_captcha(self.captcha_path)

        if not captcha_text:
            self.log("❌ Captcha recognition failed")
            return False

        self.log(f"🔤 Captcha recognized as: {captcha_text}")

        try:
            captcha_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "input_4"))
            )
            captcha_input.clear()
            captcha_input.send_keys(captcha_text)

            send_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "input_1"))
            )

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", send_btn
            )
            time.sleep(0.5)
            send_btn.click()

            return True

        except Exception as e:
            self.log(f"⚠️ Submit failed: {e}")
            return False

    # =========================
    # STRICT SUBMISSION WAIT
    # =========================
    def wait_for_captcha_and_submit(self):
        self.log("🤖 Auto-solving captcha...")

        last_attempt_time = 0
        submitted = False

        while True:
            # ✅ THANK YOU PAGE
            try:
                confirmation = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'Your submission has been received')]")
                    )
                )

                if confirmation.is_displayed():
                    self.log("✅ CONFIRMED: Submission successful")

                    # 🕒 Stay on Thank You page
                    time.sleep(3)

                    self.cleanup_after_success()
                    self.open_form()
                    return True

            except:
                pass

            # Update captcha if refreshed
            previous_src = self.last_captcha_src
            self.capture_or_update_captcha()

            if self.last_captcha_src != previous_src:
                submitted = False
                self.log("🔁 New captcha detected")

            # Attempt submit ONCE per captcha
            if not submitted and time.time() - last_attempt_time > 3:
                if self.solve_and_submit_captcha():
                    submitted = True
                last_attempt_time = time.time()

            time.sleep(1)

    # =========================
    # CLEANUP
    # =========================
    def cleanup_after_success(self):
        if os.path.exists(self.captcha_path):
            os.remove(self.captcha_path)
            self.log("🧹 Captcha image removed")

        self.driver.delete_all_cookies()
        self.driver.execute_script("window.localStorage.clear();")
        self.driver.execute_script("window.sessionStorage.clear();")
        self.log("🧹 Browser data cleared")

        self.last_captcha_src = None

    def close(self):
        self.driver.quit()
