import utils
import discord
import json
import os
from dotenv import load_dotenv
import asyncio
import datetime
import calendar


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


async def checkmail(channel, old_mails={}):
    print("Checking for mails "+str(datetime.datetime.now()))
    new_mails = utils.fetch_circulars()
    for m in new_mails:
        if m not in old_mails:
            await channel.send("**"+str(m)[:400]+"**"+'\n'+str(new_mails[m])[:1500])
    await asyncio.sleep(60)
    await checkmail(channel, new_mails)


async def set(message, id, kerberos):
    user = await message.guild.fetch_member(int(id))
    id = str(id)
    kerberos = str(kerberos)
    if kerberos in utils.kerberos_lookup:
        discord_ids = json.load(open("discord_ids.json"))
        if id in discord_ids:
            if user.name != discord_ids[id]['username'] or kerberos != discord_ids[id]['kerberos']:
                await message.reply("**INFO:** Kerberos for `"+discord_ids[id]['username']+"` was previously set to `"+discord_ids[id]['kerberos']+"`")
            else:
                await message.reply("Updating details for "+user.name)
        discord_ids.update({id : {'username':str(user.name), 'kerberos':str(kerberos)}})
        with open("discord_ids.json", "w") as outfile:
            json.dump(discord_ids, outfile)

        name = str(utils.kerberos_lookup[kerberos]["name"])
        try:
            await user.edit(nick = name)
        except:
            await message.reply("Insufficient permissions to change nick")

        year = "20"+str(kerberos[3:5])
        for y in utils.years:
            if discord.utils.get(message.guild.roles, name = y) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = y))  
        try:
            await user.add_roles(discord.utils.get(message.guild.roles, name = year))
        except:
            await message.reply("No role exists for `"+year+"`. Please request admin to create")

        hostel = str(utils.kerberos_lookup[kerberos]["hostel"])
        for h in utils.hostels:
            if discord.utils.get(message.guild.roles, name = h) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = h))  
        try:
            await user.add_roles(discord.utils.get(message.guild.roles, name = hostel))
        except:
            await message.reply("No role exists for `"+hostel+"`. Please request admin to create")

        branch = str(kerberos[:3]).upper()
        for b in utils.branches:
            if discord.utils.get(message.guild.roles, name = b.upper()) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = b.upper()))
        try:
            await user.add_roles(discord.utils.get(message.guild.roles, name = branch))
        except:
            await message.reply("No role exists for `"+branch+"`. Please request admin to create")

        course = utils.get_student_courses(kerberos)
        for c in utils.courses:
            if discord.utils.get(message.guild.roles, name = c) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = c))
        for c in course:
            try:
                await user.add_roles(discord.utils.get(message.guild.roles, name = c))
            except:
                await message.reply("No role exists for `"+c+"`. Please request admin to create")
    else:
        await message.reply("Could not find `"+kerberos+"` in kerberos database.")


async def update(message):
    discord_ids = json.load(open("discord_ids.json"))
    logs = []
    kerb_id = {}
    async for user in message.guild.fetch_members(limit=None):
        id = str(user.id)
        if id not in discord_ids:
            if discord.utils.get(message.guild.roles, name = "Bot") not in user.roles:
                logs.append("ERROR: Did not find `"+user.name+"` in discord_ids"+'\n')
            continue
        kerberos = str(discord_ids[id]['kerberos'])
        if kerberos in kerb_id:
            logs.append("WARNING: DUPLICATE key `"+kerberos+"` for `"+user.name+"` and `"+discord_ids[kerb_id[kerberos]]['kerberos']+"`\n")
        else:
            kerb_id[kerberos] = id
        if kerberos in utils.kerberos_lookup:
            name = str(utils.kerberos_lookup[kerberos]["name"])
            if name != user.nick and name != user.name:
                logs.append("WARNING: NICK for `"+user.name+"` expected: `"+name+"`, found: `"+str(user.nick)+"`\n")

            year = "20"+str(kerberos[3:5])
            for y in utils.years:
                if y != year and discord.utils.get(message.guild.roles, name = y) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = y))
                    logs.append("ACTION: Removed role `"+y+"` for `"+user.name+"`\n")
            if discord.utils.get(message.guild.roles, name = year) not in user.roles:
                try:
                    await user.add_roles(discord.utils.get(message.guild.roles, name = year))
                    logs.append("ACTION: Added role `"+year+"` for `"+user.name+"`\n")
                except:
                    logs.append("WARNING: ROLE not found `"+year+"`"+'\n')

            hostel = str(utils.kerberos_lookup[kerberos]["hostel"])
            for h in utils.hostels:
                if h != hostel and discord.utils.get(message.guild.roles, name = h) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = h))
                    logs.append("ACTION: Removed role `"+h+"` for `"+user.name+"`\n")
            if discord.utils.get(message.guild.roles, name = hostel) not in user.roles:
                try:
                    await user.add_roles(discord.utils.get(message.guild.roles, name = hostel))
                    logs.append("ACTION: Added role `"+hostel+"` for `"+user.name+"`\n")
                except:
                    logs.append("WARNING: ROLE not found `"+hostel+"`"+'\n')

            branch = str(kerberos[:3]).upper()
            for b in utils.branches:
                if b.upper() != branch and discord.utils.get(message.guild.roles, name = b.upper()) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = b.upper()))
                    logs.append("ACTION: Removed role `"+b.upper()+"` for `"+user.name+"`\n")
            if discord.utils.get(message.guild.roles, name = branch) not in user.roles:
                try:
                    await user.add_roles(discord.utils.get(message.guild.roles, name = branch))
                    logs.append("ACTION: Added role `"+branch+"` for `"+user.name+"`\n")
                except:
                    logs.append("WARNING: ROLE not found `"+branch+"`"+'\n')

            course = utils.get_student_courses(kerberos)
            for c in utils.courses:
                if c not in course and discord.utils.get(message.guild.roles, name = c) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = c))
                    logs.append("ACTION: Removed role `"+c+"` for `"+user.name+"`\n")
            for c in course:
                if discord.utils.get(message.guild.roles, name = c) not in user.roles:
                    try:
                        await user.add_roles(discord.utils.get(message.guild.roles, name = c))
                        logs.append("ACTION: Added role `"+c+"` for `"+user.name+"`\n")
                    except:
                        logs.append("WARNING: ROLE not found `"+c+"`"+'\n')
        else:
            logs.append("ERROR: Could not find `"+kerberos+"` in kerberos database"+'\n')
    return logs

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith("hello"):
        await message.reply("hello")

    if message.content.lower().startswith("?help"):
        await message.reply(
"""
**Commands**
- `hello` to check if bot is online
- `?help` to display this message
- `?set <kerberos>` to set your kerberos and automatically assign role for branch, hostel and courses
- `?courses` (self) or `?courses <kerberos>` or `?courses @User` to list courses
- `?slot <course>` to get slot for a course
- `?tt` (self) or `?tt <kerberos>` or `?tt @User` to get yours or someone else's timetable (excluding labs for now)
- `?major` (self) or `?major <kerberos>` or `?major @User` to get yours or someone else's major exam datesheet
- `?mess` (self)(today) or `?mess <hostel> -<day>` to get mess menu for the hostel on that day
- Works for multiple inputs too! Try `?slot COL106 COL202`

_Manager only_ -
- `?edit <kerberos> @User` to edit kerberos for some user
- `?checkmail #Channel` to track circular emails on that channel every minute
- `?update` to update roles for all registered users
- `?reload` to reload the database from `.csv` and `.json` files
- `?fetchldap` to fetch courses data from ldap and reload

Curious how this works? Check out the source code at https://github.com/as1605/IITD-Bot 
and leave a :star: if you like it
""")

    if message.content.lower().startswith("?set"):
        command = message.content.lower().split()
        try:
            kerberos = command[1]
            await set(message, message.author.id, kerberos)
        except:
            await message.reply("Command is `?set <kerberos>`")

    if message.content.lower().startswith("?courses"):
        command = message.content.lower().split()
        try:
            kerberos = []
            users = json.load(open("discord_ids.json"))
            for id in message.raw_mentions:
                kerberos.append(users[str(id)]["kerberos"])
            for k in command:
                if k[0].isalnum():
                    kerberos.append(k)
            if len(kerberos) == 0:
                kerberos.append(users[str(message.author.id)]["kerberos"])
            for k in kerberos:
                courses = ' '
                for c in utils.get_student_courses(k):
                    courses += c + ' '
                await message.reply(k+" `"+courses+"`")
        except:
            await message.reply("Command is `?courses` (self) or `?courses <kerberos>` or `?courses @User`")

    if message.content.lower().startswith("?slot"):
        command = message.content.upper().split()
        try:
            for course in command:
                if course.isalnum():
                    await message.reply(course+" `"+utils.course_slots[course]+"`")
        except:
            await message.reply("Command is `?slot <course>`")

    if message.content.lower().startswith("?tt"):
        command = message.content.lower().split()
        try:
            kerberos = []
            users = json.load(open("discord_ids.json"))
            for id in message.raw_mentions:
                kerberos.append(users[str(id)]["kerberos"])
            for k in command:
                if k[0].isalnum():
                    kerberos.append(k)
            if len(kerberos) == 0:
                kerberos.append(users[str(message.author.id)]["kerberos"])
            for k in kerberos:
                await message.reply(k+"\n```\n"+utils.createTimeTable(k)+"\n```") 
        except:
            await message.reply("Command is `?tt` (self) or `?tt <kerberos>` or `?tt @User`")
    
    if message.content.lower().startswith("?major"):
        command = message.content.lower().split()
        try:
            kerberos = []
            users = json.load(open("discord_ids.json"))
            for id in message.raw_mentions:
                kerberos.append(users[str(id)]["kerberos"])
            for k in command:
                if k[0].isalnum():
                    kerberos.append(k)
            if len(kerberos) == 0:
                kerberos.append(users[str(message.author.id)]["kerberos"])
            for k in kerberos:
                await message.reply(k+"\n```\n"+utils.getMajor(k)+"\n```") 
        except:
            await message.reply("Command is `?major` (self) or `?major <kerberos>` or `?major @User`")
    
    
    if message.content.lower().startswith("?mess"):
        command = message.content.title().split()
        try:
            hostel = []
            days = []
            
            for c in command:
                if c in utils.hostels:
                    hostel.append(c)
            if len(hostel) == 0:
                kerberos = json.load(open("discord_ids.json"))[str(message.author.id)]["kerberos"]
                hostel.append(utils.kerberos_lookup[kerberos]["hostel"])
            
            for c in command:
                if c[0] == '-':
                    if c.startswith("-All"):
                        days = list(range(7))
                        break
                    days.append(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].index(c[1:4]))
            if len(days) == 0:
                days.append(datetime.datetime.now().weekday())
            
            for h in hostel:
                for d in days:
                    await message.reply("`"+h+"` `"+calendar.day_name[d]+"` \n```\n"+'\n'.join(utils.mess[h][d])+" \n```")
        except:
            await message.reply("Command is `?mess` (self) or `?mess <hostel> -<day>`")

    if message.content.lower().startswith("?edit"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            try:
                id = message.raw_mentions[0]
                kerberos = message.content.lower().split()[1]
                await set(message, id, kerberos)
            except:
                await message.reply("Command is ?edit <kerberos> @User")
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?checkmail"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            for c in message.raw_channel_mentions:
                channel = message.guild.get_channel(c)
                await message.reply("Tracking mail on <#"+str(channel.id)+">")
                await checkmail(channel)
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?update"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            with open('log.txt', 'w') as f:
                f.writelines(await update(message))
                await message.reply(file= discord.File('log.txt'))
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?reload"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            utils.reload()
            await message.reply("Reloaded database")
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?fetchldap"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            try:
                utils.get_course_lists()
                utils.reload()
                await message.reply("Fetched LDAP")
            except:
                await message.reply("Host not connected to IITD Internal Network")
        else:
            await message.reply("Only server managers can use this command")


utils.reload()
load_dotenv()
client.run(os.getenv('BOT_TOKEN'))