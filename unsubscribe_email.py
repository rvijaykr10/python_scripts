import os
from dotenv import load_dotenv
import imaplib
import email
from bs4 import BeautifulSoup
import requests

load_dotenv()

username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")


def connect_to_mail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)  # type: ignore
    mail.select("inbox")
    return mail


def extract_links_from_html(html_content):  # type: ignore
    soup = BeautifulSoup(html_content, "html.parser")  # type: ignore
    links = [
        link["href"]
        for link in soup.find_all("a", href=True)
        if "unsubscribe" in link["href"].lower()
    ]
    return links


def click_link(link):  # type: ignore
    try:
        response = requests.get(link)  # type: ignore
        if response.status_code == 200:
            print("Successfully visited", link)  # type: ignore
        else:
            print("Failed to visit", link, "error code", response.status_code)  # type: ignore
    except Exception as e:
        print("Error with", link, str(e))  # type: ignore


def search_for_email():  # type: ignore
    mail = connect_to_mail()
    _, search_data = mail.search(None, '(BODY "unsubscribe")')
    data = search_data[0].split()

    links = []

    for num in data:
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])  # type: ignore
        print(msg)

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    # Get the charset of the email part
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        html_content = part.get_payload(decode=True).decode(charset, errors="replace")  # type: ignore
                        links.extend(extract_links_from_html(html_content))  # type: ignore
                    except UnicodeDecodeError as e:
                        print(f"Error decoding part: {e}")
        else:
            content_type = msg.get_content_type()
            if content_type == "text/html":
                charset = msg.get_content_charset() or "utf-8"
                try:
                    content = msg.get_payload(decode=True).decode(charset, errors="replace")  # type: ignore
                    links.extend(extract_links_from_html(content))  # type: ignore
                except UnicodeDecodeError as e:
                    print(f"Error decoding content: {e}")

            if content_type == "text/html":
                print(content_type)

    mail.logout()
    return links  # type: ignore


def save_links(links):  # type: ignore
    with open("links.txt", "w") as f:
        f.write("\n".join(links))  # type: ignore


links = search_for_email()  # type: ignore
for link in links:  # type: ignore
    click_link(link)  # type: ignore

save_links(links)
