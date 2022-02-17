import json
from urllib import response
from bs4 import BeautifulSoup
import requests
import csv
import email
import imaplib
import os
from dotenv import load_dotenv


course_lists = {}
kerberos_lookup = {}
course_slots = {}
# mess = {}
hostels = []
branches = []
courses = []
years = ["2017", "2018", "2019", "2020", "2021", "2022"]
days = []


def reload():
    global days
    days = []
    days = json.load(open("day_slots.json"))

    # global mess
    # mess = {}
    # mess = json.load(open("mess.json"))

    global course_lists
    course_lists = {}
    course_lists = json.load(open("course_lists.json"))

    global course_slots
    course_slots = {}
    course_slots = json.load(open("course_slots.json"))

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
    soup = BeautifulSoup(response.text,'html.parser')
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
        soup = BeautifulSoup(response.text, 'html.parser')
        students = soup.find_all('td', attrs = {'align' : 'LEFT'})
        sList = []
        for s in students:
            sList.append(s.text)
        courseLists[course.text] = sList
    with open("course_lists.json", "w") as outfile:
        json.dump(courseLists, outfile)


def get_course_slots():
    course_slots = {}
    with open('Courses_Offered.csv', newline='') as csvfile:
        sheet = csv.reader(csvfile, delimiter=',')
        for s in sheet:
            course = s[1].split('-')[-1]
            #if course in course_lists:
            slot = s[3]
            course_slots[course] = slot
    with open("course_slots.json", "w") as outfile:
        json.dump(course_slots, outfile)


def get_student_courses(kerberos):
    courses = []
    for c in course_lists:
        if kerberos in course_lists[c]:
            courses.append(c)
    return courses


def fetch_circulars(to = 'allstudents@circular.iitd.ac.in'):
    try:
        load_dotenv()
    except:
        print("ERROR: Failed to load dotenv!")
        return {}
    IITD_EMAIL = os.getenv('IITD_EMAIL')
    IITD_PASS = os.getenv('IITD_PASS')
    SERVER = 'mailstore.iitd.ac.in'
    try:
        mail = imaplib.IMAP4_SSL(SERVER)
        mail.login(IITD_EMAIL, IITD_PASS)
        mail.select('inbox', readonly=True)
        status, data = mail.search(None, 'ALL')
    except:
        print("ERROR: Network connection failed!")
        return {}
    mail_ids = []
    for block in data:
        mail_ids += block.split()
    new_mails = {}
    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                if to not in message['X-Original-To']:
                    continue
                mail_subject = message['subject']
                print("SUBJECT: " + mail_subject)
                if message.is_multipart():
                    mail_content = ''
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload(decode=True).decode('utf-8')
                else:
                    mail_content = message.get_payload()
                new_mails[mail_subject] = mail_content
    return new_mails

#PROGRAM TO CREATE COURSES TIMETABLE 
def createTimeTable(kerberos): 
    timetable = [[] for i in range(5)]
    for course in get_student_courses(kerberos):
        if kerberos[4] != '1':
            course = course[5:]
        try : 
            slot = course_slots[course]
            for i in range(5): 
                if slot in days[i]:
                    timetable[i].append((slot,course,days[i][slot]))
                timetable[i].sort()
        except:
            print(course+" Not found")
    week = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    tt = ""
    for i in range(5):
        tt+=week[i]+'\n'
        for tup in timetable[i]:
            tt+=tup[2] + ": " + tup[1] +'\n'
        tt+='\n'
    return tt


def mess_menu(hostel):
    url = 'https://jasrajsb.github.io/iitd-api/v1/mess-menu/' + hostel.lower() + '.json'
    headers = {'user-agent': 'iitd-bot/1.0.0'}
    response = requests.get(url, headers=headers)

    menu = {}
    for r in response.json():
        menu[r["day"][:3]] = r["menu"]

    return menu


reload()