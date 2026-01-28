# Batch Automation & Data Integration Bot

## Overview

This project is a **batch automation bot** that automatically submits data to a Jotform form for multiple users. The bot reads user records from an Excel file, fills the form fields, **solves image-based captchas using a CNN-based image recognizer**, submits the form, verifies successful submission, and then proceeds to the next record.

The project demonstrates:

* Browser automation using Selenium
* Batch data processing from Excel
* Image-based captcha recognition (proof-of-concept)
* Robust submission validation and retry handling

Target form URL:

```
https://form.jotform.com/260231667243453
```

---

## Project Structure

```
project-root/
│
├── bot.py                 # Main automation bot
├── recognize_image.py     # Captcha image recognizer module
├── embeddings.pkl         # Precomputed image embeddings database
├── dataset/               # Captcha reference images (used to build embeddings)
├── captcha/               # Runtime captcha images (auto-generated)
├── sample_data.xlsx       # Sample Excel input file
├── requirements.txt       # Project dependencies
└── README.md              # This file
```

---

## Environment Setup

### 1. Python Version

* **Python 3.9 or later** is recommended

Check your version:

```bash
python --version
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate it:

* **Windows**

```bash
venv\Scripts\activate
```

* **macOS / Linux**

```bash
source venv/bin/activate
```

---

## Dependencies Installation

Install all required packages using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Dependency Overview

| Package      | Purpose                                    |
| ------------ | ------------------------------------------ |
| selenium     | Browser automation                         |
| pandas       | Excel file processing                      |
| openpyxl     | Excel (.xlsx) support                      |
| pillow       | Image handling                             |
| torch        | Deep learning framework                    |
| torchvision  | Pretrained ResNet model                    |
| scikit-learn | Cosine similarity computation              |
| pyside6      | GUI support (if using a desktop interface) |

---

## Browser & Driver Setup

### Google Chrome

* Ensure **Google Chrome** is installed
* Check version:

```bash
chrome://settings/help
```

### ChromeDriver

* Download **ChromeDriver** matching your Chrome version
* Place `chromedriver.exe` in project root or add to system PATH
* Download link:

```
https://chromedriver.chromium.org/downloads
```

---

## Excel Input File Format

Each row represents **one form submission**.

### Required Columns

| Column Name   | Description                              |
| ------------- | ---------------------------------------- |
| FirstName     | First name                               |
| LastName      | Last name                                |
| Phone         | 10-digit phone number                    |
| Email         | Email address                            |
| ContactMethod | Dropdown value (must match form options) |
| HowFound      | Dropdown value (must match form options) |
| Reason        | Message text                             |

📌 **Important:** Dropdown values must match the form’s visible text exactly.

A sample file (`sample_data.xlsx`) is included.

---

## Captcha Recognition (Important Note)

This project uses a **CNN-based image embedding approach (ResNet18)** to recognize captcha images.

### How it works

1. Captcha images are saved locally at runtime
2. Images are converted into feature embeddings
3. Cosine similarity is used to match against a known dataset
4. The predicted captcha text is derived from the closest match

### Disclaimer

> This captcha recognition system is implemented as a **proof-of-concept** for technical demonstration purposes. It assumes a closed or repeatable captcha image set and is **not intended to bypass production-grade anti-bot systems**.

---

## Running the Bot

1. Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

2. Place your Excel file (`sample_data.xlsx` or custom) in the project directory

3. Start the bot:

```bash
python app.py
```

### Workflow

```
Load Excel → Fill Form → Solve Captcha → Submit → Verify → Wait 3s on Thank You page → Reload → Next Record
```

During execution, the bot will:

* Display live logs
* Save captcha images to `captcha/`
* Automatically retry on captcha refresh
* Fill and submit all records sequentially

---

## Success Detection

A submission is considered **successful only when** the following message appears:

```
Your submission has been received
```

After success:

* Bot waits **3 seconds** on the Thank You page
* Browser storage is cleared
* Form reloads for the next record

---

## Troubleshooting

### Captcha Not Recognized

* Ensure `embeddings.pkl` exists
* Ensure captcha image is being saved correctly

### Form Resets Unexpectedly

* Verify submit button selector (`id="input_1"`)
* Ensure captcha recognition timing is correct

### ChromeDriver Errors

* Confirm ChromeDriver version matches Chrome

---

## Deliverables Checklist

✔ Source code
✔ Sample Excel file
✔ Captcha embeddings database
✔ Screen recording demonstrating:

* File selection
* At least 3 consecutive submissions
* Successful captcha handling

---

## Final Notes

This project demonstrates **automation reliability, ML integration, and defensive scripting practices** suitable for real-world batch processing tasks.

The codebase is structured for **easy customization and extension**.
