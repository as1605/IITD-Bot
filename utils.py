import json
from bs4 import BeautifulSoup
import requests
import csv
import email
import imaplib
import os
from dotenv import load_dotenv


course_lists = {}
kerberos_lookup = {}
hostels = []
branches = []
courses = []


def reload():
    global course_lists
    course_lists = {}
    course_lists = json.load(open("course_lists.json"))

    global kerberos_lookup
    kerberos_lookup = {}
    with open('kerberos.csv', newline='') as csvfile:
        sheet = csv.reader(csvfile, delimiter=',')
        for s in sheet:
            kerberos_lookup[s[0]] = {'name' : s[1], 'hostel' : s[2]}

    global hostels
    hostels = []
    with open('hostels.csv', newline='') as csvfile:
        sheet = csv.reader(csvfile, delimiter=',')
        for s in sheet:
            hostels.append(s[0])

    global branches
    branches = []
    with open('branches.csv', newline='') as csvfile:
        sheet = csv.reader(csvfile, delimiter=',')
        for s in sheet:
            branches.append(s[0])

    global courses
    courses = []
    with open('courses.csv', newline='') as csvfile:
        sheet = csv.reader(csvfile, delimiter=',')
        for s in sheet:
            courses.append(s[0])


def get_course_lists():
    url = "http://ldap1.iitd.ernet.in/LDAP/courses/gpaliases.html"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch "+url+" Status "+response.status_code)
        return
    soup = BeautifulSoup(response.text,'lxml')
    courses = soup.find_all('a')
    courseLists = {}
    for course in courses:
        url = "http://ldap1.iitd.ernet.in/LDAP/courses/"+course['href']
        if url is None:
            print("Failed to get "+str(course))
            continue
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to fetch " + url + " Status " + response.status_code)
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        students = soup.find_all('td', attrs = {'align' : 'LEFT'})
        sList = []
        for s in students:
            sList.append(s.text)
        courseLists[course.text] = sList
    with open("course_lists.json", "w") as outfile:
        json.dump(courseLists, outfile)


def get_student_courses(kerberos):
    courses = []
    for c in course_lists:
        if kerberos in course_lists[c]:
            courses.append(c)
    return courses


def fetch_circulars():
    load_dotenv()
    IITD_EMAIL = os.getenv('IITD_EMAIL')
    IITD_PASS = os.getenv('IITD_PASS')
    SERVER = 'mailstore.iitd.ac.in'
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(IITD_EMAIL, IITD_PASS)
    mail.select('inbox')
    status, data = mail.search(None, 'ALL')
    mail_ids = []
    for block in data:
        mail_ids += block.split()
    new_mails = {}
    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                if 'allstudents@circular.iitd.ac.in' not in message['X-Original-To']:
                    continue
                mail_subject = message['subject']
                if message.is_multipart():
                    mail_content = ''
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    mail_content = message.get_payload()
                new_mails[mail_subject] = mail_content
    return new_mails

