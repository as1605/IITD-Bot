import datetime
from . import utils
from . import chat
import discord
import json
import os
from dotenv import load_dotenv
import calendar


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


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
        await chat.help(message=message)

    if message.content.lower().startswith("?set"):
        command = message.content.lower().split()
        try:
            kerberos = command[1]
            await chat.set(message, message.author.id, kerberos)
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
                await message.reply(f"{k} `{courses}`")
        except:
            await message.reply("Command is `?courses` (self) or `?courses <kerberos>` or `?courses @User`")

    if message.content.lower().startswith("?slot"):
        command = message.content.upper().split()
        try:
            for course in command:
                if course.isalnum():
                    await message.reply(f"{course} `{utils.course_slots[course]}`")
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
                await message.reply(f"{k}\n```\n{utils.createTimeTable(k)}\n```") 
        except:
            await message.reply("Command is `?tt` (self) or `?tt <kerberos>` or `?tt @User`")

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
                    await message.reply(f"`{h}` `{calendar.day_name[d]}` \n```\n{'\n'.join(utils.mess[h][d])} \n```")
        except:
            await message.reply("Command is `?mess` (self) or `?mess <hostel> -<day>`")


    if message.content.lower().startswith("?edit"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            try:
                id = message.raw_mentions[0]
                kerberos = message.content.lower().split()[1]
                await chat.set(message, id, kerberos)
            except:
                await message.reply("Command is ?edit <kerberos> @User")
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?checkmail"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            to = message.content.lower().split()[1]
            for c in message.raw_channel_mentions:
                channel = message.guild.get_channel(c)
                await message.reply(f"Tracking mail to `{to}` on <#{str(channel.id)}>")
                await chat.checkmail(channel, to)
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?update"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            await chat.update(message, open('log.txt', 'w'))
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