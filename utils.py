import json
from bs4 import BeautifulSoup
import requests
import csv
import email
import imaplib
import os
from dotenv import load_dotenv
import datetime


course_lists = {}
kerberos_lookup = {}
course_slots = {}
# mess = {}
hostels = []
groups = {}
branches = []
courses = []
courseinfo = {}
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

    global groups
    groups = {}
    groups = json.load(open("groups.json"))

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

    global courseinfo
    courseinfo = {}
    with open("raw_course_data_2.xml") as cdata:
        s = "".join(cdata.readlines())
        tree = BeautifulSoup(s, 'lxml')

    # handling missing courses as well: 
    mscidx = 0
    for dep in tree.findAll("courses"):
        for course in dep.findAll("course"):
            ccode = getattr(course.find("code"), "string", None)
            if not ccode:
                ccode = f"MISS{mscidx}"
                mscidx += 1

            courseinfo[ccode] = {
                "code": ccode,
                "name": getattr(course.find("name"), "string", None),
                "credits": getattr(course.find("credits"), "string", None),
                "credit-structure": getattr(course.find("credit-structure"), "string", None),
                "pre-requisites": getattr(course.find("pre-requisites"), "string", None),
                "overlap": getattr(course.find("overlap"), "string", None),
                "department": dep.get("department"),
                "description": getattr(course.find("description"), "string", None)
            }

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
        if c[:4] != "2102":
            continue
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

def createTimeTable(kerberos): 
    timetable = [[] for i in range(5)]
    for course in get_student_courses(kerberos):
        # if kerberos[4] != '1':
        course = course[5:]
        try : 
            if kerberos in groups:
                slot1 = "2102-"+course[:6]+"-G"+str(groups[kerberos])
                slot2 = "2102-"+course[:6]+"-T"+str(groups[kerberos])
                slot3 = "2102-"+course[:6]+"-G"+str(groups[kerberos])+"W"+str(datetime.datetime.now().isocalendar()[1]-11)
                for i in range(5): 
                    if slot1 in days[i]:
                        timetable[i].append((slot1[5:],days[i][slot1]))
                    if slot2 in days[i]:
                        timetable[i].append((slot2[5:],days[i][slot2]))
                    if slot3 in days[i]:
                        timetable[i].append((slot3[5:],days[i][slot3]))
                    timetable[i].sort()
            if course in course_slots:
                slot = course_slots[course]
                for i in range(5): 
                    if slot in days[i]:
                        timetable[i].append((course,days[i][slot]))
                    timetable[i].sort()
        except:
            print(course+" Not found")
    week = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    tt = []
    for i in range(5):
        s = "```"
        for tup in timetable[i]:
            s+=tup[0] + ": " + tup[1] +'\n'
        s+="```"
        tt.append((week[i], s))
    return tt

def mess_menu(hostel):
    url = 'https://jasrajsb.github.io/iitd-api/v1/mess-menu/' + hostel.lower() + '.json'
    headers = {'user-agent': 'iitd-bot/1.0.0'}
    response = requests.get(url, headers=headers)

    menu = {}
    for r in response.json():
        menu[r["day"][:3]] = r["menu"]

    return menu

def mess_sheet(hostel):
    id = json.load(open('mess_links.json'))[hostel.title()].split('/')[-2]
    url = 'https://docs.google.com/spreadsheets/d/' + id + '/export?format=tsv'
    response = requests.get(url)
    table = [a.split('\t') for a in response.text.split('\r\n')]
    days = table[0][5:12]
    menu = {}
    for i in range(5,12):
        day = table[0][i][:3]
        meals = []
        for r in table:
            if r[0] == '':
                continue
            meal = {}
            meal['name'] = r[0]
            meal['time'] = f"{r[1]} {r[2]} - {r[3]} {r[4]}"
            meal['menu'] = r[i]
            meals.append(meal)
        menu[day] = meals
    return menu

def course_info(code):
    code = code.upper()
    if code not in courseinfo:
        return code + " cannot be found!"
    course = courseinfo[code]
    dependencies = []
    for c in courseinfo:
        if code in str(courseinfo[c]['pre-requisites']):
            dependencies.append(c)
    course['dependencies'] = dependencies
    return course

def yt(vc, token):
    # https://discord.com/developers/docs/resources/channel#create-channel-invite
    invite = requests.post('https://discord.com/api/v8/channels/' + vc + '/invites',
        headers = { 'Authorization' : 'Bot ' + token },
        json = {
            'max_age': 604800,
            'max_uses': 0,
            'target_application_id': 880218394199220334,
            'target_type': 2,
            'temporary': False,
            'unique': False,
            'validate': None
        })
    if (invite.status_code != 200):
        raise Exception(invite.text)
    return 'https://discord.com/invite/'+invite.json()['code']

def generateGroups():
    file = json.load(open('course_lists.json'))
    groups = {}
    for course in file:
        if course[:7] == "MTL100T":
            group = int(course[7:])
            print(group)
            for kerberos in file[course]:
                groups[kerberos] = group
    json.dump(groups, open('mtl_groups.json', 'w+'))

def mergePYLGroups():
    out = {}
    file = open('batchB.csv')
    sheet = csv.reader(file)
    out = json.load(open('mtl_groups.json'))
    for s in sheet:
        out[s[0]] = int(s[1])
    json.dump(out, open('groups.json', 'w'))

def major_tt(kerberos):
    courses = get_student_courses(kerberos)
    url = "https://aditm7.github.io/Majors_api/majors.json"
    headers = {'user-agent': 'iitd-bot/1.0.0'}
    majors_info = requests.get(url, headers=headers).json()
    tt = {}
    for c in courses:
        c=c[5:11]
        try:
            m = majors_info[c]
            if m["Day"] not in tt:
                tt[m["Day"]] = []
            tt[m["Day"]].append([m["Time"].zfill(11), '/'.join(m["LHCs"]), c])
            tt[m["Day"]].sort()
        except:
            if 0 not in tt:
                tt[0] = []
            tt[0].append(["?", "?", c])
            tt[0].sort()
    return dict(sorted(tt.items()))


reload()
