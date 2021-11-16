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
course_slots = {}
mess = {}
hostels = []
branches = []
courses = []
years = ["2017", "2018", "2019", "2020", "2021", "2022"]


def reload():
    global mess
    mess = {}
    mess = json.load(open("mess.json"))

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
            course = s[1].split('-')[-1][:6]
            if course in course_lists:
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


def fetch_circulars():
    load_dotenv()
    IITD_EMAIL = os.getenv('IITD_EMAIL')
    IITD_PASS = os.getenv('IITD_PASS')
    SERVER = 'mailstore.iitd.ac.in'
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(IITD_EMAIL, IITD_PASS)
    mail.select('inbox', readonly=True)
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
                    if 'allbtech@circular.iitd.ac.in' not in message['X-Original-To']:
                        if 'alldual@circular.iitd.ac.in' not in message['X-Original-To']:
                            if 'allintegrated@circular.iitd.ac.in' not in message['X-Original-To']:
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

days = {
    0 : {
        "A" : "8-9:30 AM",
        "B" : "9:30-11AM",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "11-12 AM ",
        "J" : "12-1 PM  ",
        "K" : "",
        "L" : "",
        "M" : "5-6:30 PM"
    },
        1 : {
        "A" : "",
        "B" : "",
        "C" : "8-9 AM   ",
        "D" : "9-10 AM  ",
        "E" : "10-11 AM ",
        "F" : "11-12 PM ",
        "H" : "",
        "J" : "12-1 PM  ",
        "K" : "5-6 PM   ",
        "L" : "6-7 PM   ",
        "M" : ""
    },
        2 : {
        "A" : "",
        "B" : "",
        "C" : "8-9 AM   ",
        "D" : "9-10 AM  ",
        "E" : "10-11 AM ",
        "F" : "",
        "H" : "11-12 PM ",
        "J" : "",
        "K" : "12-1 PM  ",
        "L" : "",
        "M" : ""
    }, 
        3 : {
        "A" : "8-9:30 AM",
        "B" : "9:30-11AM",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "11-12 AM ",
        "H" : "12-1 PM  ",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "5-6:30 PM"
    },
        4 : {
        "A" : "",
        "B" : "",
        "C" : "8-9 AM   ",
        "D" : "9-10 AM  ",
        "E" : "10-11 AM ",
        "F" : "11-12 PM ",
        "H" : "",
        "J" : "12-1 PM  ",
        "K" : "5-6 PM   ",
        "L" : "6-7 PM   ",
        "M" : ""
    }
}



major_days = {
    15 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "End time 12:00/16:00",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },
    16 : {
        "A" : "",
        "B" : "End time 12:00/16:00",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },
    17 : {
        "A" : "End time 12:00",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },
    18 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "End time 12:00/16:00",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },    
    19 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },  
    20 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "End time 16:00/20:00",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },
    21 : {
        "A" : "",
        "B" : "",
        "C" : "End time 12:00",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },
    22 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "End time 12:00",
        "J" : "",
        "K" : "",
        "L" : "",
        "M" : "",
    },
    23 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "",
        "K" : "End time 16:00",
        "L" : "",
        "M" : "End time 12:00",
    },
    24 : {
        "A" : "",
        "B" : "",
        "C" : "",
        "D" : "",
        "E" : "",
        "F" : "",
        "H" : "",
        "J" : "End time 12:00",
        "K" : "",
        "L" : "",
        "M" : "",
    },
}

def createTimeTable(kerberos): 
    timetable = [[] for i in range(5)]
    for course in get_student_courses(kerberos):
        try : 
            slot = course_slots[course[:6]]
            for i in range(5): 
                if days[i][slot] != "":
                    timetable[i].append((slot,course,days[i][slot]))
                timetable[i].sort()
        except:
            print(course+" Not found")
    week = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    tt = ""
    for i in range(5):
        tt+=week[i]+'\n'
        for tup in timetable[i]:
            tt+=tup[2] + ": " + tup[1] + ' ('+ tup[0] + ')' +'\n'
        tt+='\n'
    return tt

def getMajor(kerberos):
    timetable = [[] for i in range(10)]
    for course in get_student_courses(kerberos):
        try : 
            slot = course_slots[course[:6]]
            for i in range(10): 
                if major_days[i+15][slot] != "":
                    timetable[i].append((slot,course,major_days[i+15][slot]))
                timetable[i].sort()
        except:
            print(course+" Not found")
    week = ["15 Nov","16 Nov","17 Nov","18 Nov","19 Nov","20 Nov","21 Nov","22 Nov","23 Nov","24 Nov"]
    tt = ""
    for i in range(10):
        if len(timetable[i]) == 0:
            continue
        tt+=week[i] + '\t'
        for tup in timetable[i]:
            tt+=tup[1] +'\t'
        tt+='\n'
    return tt 