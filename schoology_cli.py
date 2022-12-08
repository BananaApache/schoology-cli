
import click
import os
import requests
from bs4 import BeautifulSoup as bs
import json
import smtplib
import datetime
from PyPDF2 import PdfFileMerger
from PIL import Image
from colorama import Fore as F

#@ DEFINING PATHS
home = os.getenv('HOME')
schoology_creds_file_path = os.path.join(home, '.archimedean', 'schoology_creds.json')
downloads_folder = os.path.join(home, 'Downloads')

#@ DEFINING STYLES FOR COOL COLORS
class styles:
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    cyan = '\u001b[36m'
    white = '\u001b[37m'
    clear = '\x1b[2K'
    line_up = '\033[1A'


@click.group()
def schoology():
    "Download your homework and classwork from Schoology from your own terminal."


@schoology.command()
def schoology_login():
    "Login to Schoology"

    print()

    username = input(
        styles.yellow + "Enter your Schoology's username or email: " + styles.white)
    password = input(
        styles.yellow + "Enter your Schoology's password: " + styles.white)

    creds = {
        "username": username,
        "password": password
    }

    open(schoology_creds_file_path, 'w+').write(json.dumps(creds, indent=4))

    print(styles.green + "\nSaved credentials. You can now login to Schoology.\n")


def get_courses(course):
    url = "https://app.schoology.com/login"
    with requests.Session() as s:
        r = s.get(url)
        soup = bs(r.content, 'html.parser')
        form_build_id = soup.find("input", attrs={"name": "form_build_id"})

        payload = {"mail": "dabbingshrekbru@gmail.com",
                   "school": '',
                   "school_nid": '',
                   "pass": "072405dl",
                   "form_build_id": form_build_id,
                   "form_id": "s_user_login_form"
                   }

        p = s.post(url, data=payload)

        r = s.get(course)
        soup = bs(r.content, 'html.parser')

        nav = {}

        for a in soup.findAll("a"):
            if str(a.parent).startswith('<div class="folder-title">') or str(a.parent).startswith('<div class="item-title">') or str(a.parent).startswith('<span class="attachments-file-name">'):
                nav.update({a.text: "https://app.schoology.com" + a['href']})

        for a in soup.findAll("a"):
            if a.text == "Up":
                nav.update(
                    {styles.green + "BACK": "https://app.schoology.com" + a['href']})

        count = 1
        for i in nav:
            print(styles.yellow, count, styles.white + i)
            count += 1

        try:
            inp = int(input(styles.white + "\nChoose where to navigate: "))
        except:
            print(styles.red + "\nInput should be a number.")
            exit()

        if inp > len(nav):
            print(styles.red + "\nInput out of range.")
            exit()

        url = list(nav.items())[inp - 1][1]
        r = s.get(url)

        if "https://app.schoology.com/assignment/" not in url and "/gp/" not in url:
            # @ For Folders
            get_courses(url)

        elif "/gp/" in url:
            # @ For PDFs
            r = s.get(url)
            soup = bs(r.content, 'html.parser')
            pdf_url = "https://app.schoology.com" + \
                soup.find("iframe", class_="docviewer-iframe")['src']
            pdf_name = soup.find("h2").text
            r = s.get(pdf_url)
            soup = bs(r.content, 'html.parser')
            javascript = list(soup.findAll(
                "script", {"type": "text/javascript"}))[0]
            pdf_id = pdf_url.split("attachment/")[1].split("/docviewer")[0]
            document_id = str(javascript).split(
                "files-cdn.schoology.com\/")[1].split("?content-type")[0]

            r = s.get(
                f"https://app.schoology.com/attachment/{pdf_id}/source/{document_id}.pdf")
            pdf = open(f"{downloads_folder}/{pdf_name}.html", 'wb')
            pdf.write(r.content)
            pdf.close()
            print("\n" + styles.cyan + pdf_name,
                  styles.white + "File Downloaded")

        else:
            # @ For Assignments
            r = s.get(url)
            soup = bs(r.content, 'html.parser')

            if soup.find("div", id="dropbox-revisions"):
                # ~ Yes Assignments submitted
                inp = input("\nView submission or instructions? (s/i) ")

                if inp == "i":
                    # ~ For Instructions
                    pdf_url = "https://app.schoology.com" + \
                        str(list(soup.find(
                            "span", class_="attachments-file-name").descendants)[0]).split("\"")[1]
                    pdf_name = soup.find("h2").text
                    r = s.get(pdf_url)
                    pdf = open(
                        f"{downloads_folder}/Instructions for {pdf_name}.pdf", 'wb')
                    pdf.write(r.content)
                    pdf.close()
                    print("\n" + styles.cyan + pdf_name,
                          styles.white + "File Downloaded")
                elif inp == "s":
                    # ~ For Submissions
                    assignment_url = "https://app.schoology.com/" + \
                        list(soup.find("li", class_="first last").descendants)[
                            0]['href']
                    r = s.get(assignment_url)
                    pdf_name = soup.find("h2").text
                    pdf_url = "https://app.schoology.com/" + \
                        bs(r.content, 'html.parser').find("iframe")['src']
                    r = s.get(pdf_url)

                    javascript = bs(r.content, 'html.parser').find(
                        "script", {"type": "text/javascript"})
                    pdf_id = pdf_url.split("submission/")[1].split("/")[0]
                    document_id = str(javascript).split(
                        "?content-type")[0].split("files-cdn.schoology.com\\/")[1]

                    r = s.get(
                        f"https://app.schoology.com/submission/{pdf_id}/source/{document_id}.pdf")
                    pdf = open(
                        f"{downloads_folder}/My_Submission_for_{pdf_name}.pdf", 'wb')
                    pdf.write(r.content)
                    pdf.close()
                    print("\n" + styles.cyan + pdf_name,
                          styles.white + "File Downloaded")

            else:
                # ~ No assignments submitted
                pdf_url = "https://app.schoology.com/" + \
                    str(list(soup.find(
                        "span", class_="attachments-file-name").descendants)[0]).split("\"")[1]
                pdf_name = soup.find("h2").text
                r = s.get(pdf_url)
                pdf = open(
                    f"{downloads_folder}/Instructions_for_{pdf_name}.pdf", 'wb')
                pdf.write(r.content)
                pdf.close()
                print("\n" + styles.cyan + pdf_name,
                      styles.white + "File Downloaded")


@schoology.command()
def download():
    "Download your submissions or instructions for assignments on Schoology."
    if not os.path.isfile(schoology_creds_file_path):
        print(styles.red + "\nRun 'archimedean schoology-login' first to save your credentials.")
        exit()

    creds = json.load(open(schoology_creds_file_path, 'r'))
    username = creds['username']
    password = creds['password']

    url = "https://app.schoology.com/login"

    with requests.Session() as s:
        r = s.get(url)
        soup = bs(r.content, 'html.parser')
        form_build_id = soup.find("input", attrs={"name": "form_build_id"})

        payload = {"mail": username,
                   "school": '',
                   "school_nid": '',
                   "pass": password,
                   "form_build_id": form_build_id,
                   "form_id": "s_user_login_form"
                   }

        p = s.post(url, data=payload)
        r = s.get("https://app.schoology.com/home")
        soup = bs(r.content, 'html.parser')

        for iframe in soup.findAll("iframe"):
            user_id = iframe['src'].split("id=")[1]

        r = s.get(f"https://app.schoology.com/user/{user_id}/info")
        soup = bs(r.content, 'html.parser')

        courses = {}
        for a in soup.findAll("a"):
            if str(a.parent).startswith('<div class="course-item-right">'):
                courses.update({a.text: "https://app.schoology.com" +
                               a['href'] + "/materials"})

        count = 1
        for course in courses:
            print(styles.yellow, count, styles.white, course)
            count += 1

        inp = int(input("\nChoose which course you want to enter: ")) - 1
        print()
        get_courses(list(courses.items())[inp][1])


schoology(prog_name='schoology')