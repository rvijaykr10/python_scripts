import os
import logging
from dotenv import load_dotenv
import imaplib
import email
from bs4 import BeautifulSoup
import requests
from charset_normalizer import detect
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("email_processing.log"), logging.StreamHandler()],
)


def connect_to_mail():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("inbox")
        print(Fore.GREEN + "[INFO] Successfully connected to the mail server.")
        return mail
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to connect to the mail server: {e}")
        raise


def decode_with_fallback(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        detected = detect(content)
        print(
            Fore.YELLOW
            + f"[WARNING] Fallback decoding used with detected encoding: {detected['encoding']}"
        )
        return content.decode(detected["encoding"], errors="replace")


def extract_links_from_html(html_content: str):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        links = [
            link["href"]
            for link in soup.find_all("a", href=True)
            if "unsubscribe" in link["href"].lower()
        ]
        print(Fore.CYAN + f"[INFO] Extracted {len(links)} unsubscribe links.")
        return links
    except Exception as e:
        print(Fore.RED + f"[ERROR] Error extracting links from HTML content: {e}")
        return []


def click_link(link: str):
    try:
        response = requests.get(link, timeout=10)
        if response.status_code == 200:
            print(Fore.GREEN + f"[INFO] Successfully visited: {link}")
        else:
            print(
                Fore.YELLOW
                + f"[WARNING] Failed to visit {link}. Status code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[ERROR] Error visiting {link}: {e}")


def safe_print_email(msg: email.message.Message):
    try:
        print(Fore.MAGENTA + f"[EMAIL INFO] From: {msg.get('From')}")
        print(Fore.MAGENTA + f"[EMAIL INFO] Subject: {msg.get('Subject')}")
    except UnicodeEncodeError as e:
        print(Fore.YELLOW + f"[WARNING] Error printing email headers: {e}")


def search_for_email():
    try:
        mail = connect_to_mail()
        _, search_data = mail.search(None, '(BODY "unsubscribe")')
        data = search_data[0].split()

        total_emails = len(data)
        print(
            Fore.BLUE + f"[INFO] Found {total_emails} emails containing 'unsubscribe'."
        )
        links = []

        for i, num in enumerate(data, start=1):
            _, email_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(email_data[0][1])
            safe_print_email(msg)

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        html_content = decode_with_fallback(
                            part.get_payload(decode=True)
                        )
                        links.extend(extract_links_from_html(html_content))
            else:
                content_type = msg.get_content_type()
                if content_type == "text/html":
                    html_content = decode_with_fallback(msg.get_payload(decode=True))
                    links.extend(extract_links_from_html(html_content))

            # Calculate and log progress
            percentage_complete = (i / total_emails) * 100
            print(
                Fore.CYAN
                + f"[PROGRESS] Processed {i}/{total_emails} emails ({percentage_complete:.2f}% complete)."
            )

        mail.logout()
        print(Fore.GREEN + "[INFO] Disconnected from the mail server.")
        return links
    except Exception as e:
        print(Fore.RED + f"[ERROR] Error searching for emails: {e}")
        return []


def save_links(links):
    try:
        with open("links.txt", "w") as f:
            f.write("\n".join(links))
        print(Fore.GREEN + f"[INFO] Saved {len(links)} links to 'links.txt'.")
    except Exception as e:
        print(Fore.RED + f"[ERROR] Error saving links to file: {e}")


if __name__ == "__main__":
    print(Fore.GREEN + "[START] Starting email processing script.")
    links = search_for_email()
    for link in links:
        click_link(link)
    save_links(links)
    print(Fore.GREEN + "[END] Email processing script completed.")
