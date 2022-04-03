import utils
import chat
import discord
import json
import os
from dotenv import load_dotenv
import datetime


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

log = []
async def checkspam(message):
    if message.content == "" or message.author.bot:
        return False
    log.append(message)
    if len(log) > 25:
        log.pop(0)
    same = []
    for l in log:
        if l.author == message.author and l.content == message.content:
            same.append(l)
    if len(same) > 3:
        for m in same:
            try:
                print(f"!ALERT!{message.guild}!{message.channel}!{message.author}!")
                with open("spam.txt", "a") as messages:
                    messages.write(f"{m}\n")
                # await m.reply("`[REDACTED]`")
                await m.delete()
            except:
                print("[ERROR] couldn't delete")
        return True
    return False


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if await checkspam(message):
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
                embed = discord.Embed(title="Courses", color=discord.Color.red())
                embed.add_field(name=k, value="\t".join(f"`{c}`" for c in utils.get_student_courses(k)))
                await message.reply(embed=embed)
        except:
            await message.reply("Command is `?courses` (self) or `?courses <kerberos>` or `?courses @User`")

    if message.content.lower().startswith("?slot"):
        command = message.content.upper().split()
        try:
            embed = discord.Embed(title="Slot", color=discord.Color.green())
            for course in command:
                if course in utils.course_slots:
                    embed.add_field(name=course, value=f"`{utils.course_slots[course]}`")
            await message.reply(embed=embed)
        except:
            await message.reply("Command is `?slot <course>`")

    if message.content.lower().startswith("?info"):
        command = message.content.upper().split()
        try:
            for course in command:
                if course in utils.courseinfo:
                    info = utils.course_info(course)
                    embed = discord.Embed(title = f"{info['code']} - {info['name']}", color=discord.Color.gold())
                    embed.add_field(name='Credits', value = f"`{info['credits']}`")
                    embed.add_field(name='Credit Structure', value = f"`{info['credit-structure']}`")
                    embed.add_field(name='Pre-requisites', value = f"`{info['pre-requisites']}`")
                    embed.add_field(name='Dependencies', value = '\t'.join(f"`{c}`" for c in info['dependencies']))
                    embed.add_field(name='Overlap', value = f"`{info['overlap']}`")
                    embed.add_field(name='Description', value = info['description'], inline=False)
                    await message.reply(embed=embed)
        except:
            await message.reply("Command is `?info <course>`")

    if message.content.lower().startswith("?tt"):
        if message.channel.name != "bot-commands":
            channel = discord.utils.get(message.guild.channels, name='bot-commands')
            await message.reply(f"Please use {channel.mention} channel")
            return
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
                embed = discord.Embed(title=f"Timetable for {k}", color=discord.Color.red())
                for day in utils.createTimeTable(k):
                    embed.add_field(name=day[0], value=day[1], inline=False)
            await message.reply(embed=embed)
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
                tt = utils.major_tt(k)
                embed = discord.Embed(title=f"Majors for {k}", color=discord.Color.green())
                for t in tt:
                    s = "\n".join(f"`{e[2]}` : **{e[0]}** ({e[1]})" for e in tt[t])
                    embed.add_field(name=f"{str(t).zfill(2)} April", value=s, inline=False)
                await message.reply(embed=embed) 
        except:
            await message.reply("Command is `?major` (self) or `?major <kerberos>` or `?major @User`")

    if message.content.lower().startswith("?mess"):
        if message.channel.name != "bot-commands":
            channel = discord.utils.get(message.guild.channels, name='bot-commands')
            await message.reply(f"Please use {channel.mention} channel")
            return
        command = message.content.title().split()
        try:
            await chat.mess(message, command)
        except:
            await message.reply("Command is `?mess` (self) or `?mess @User` or `?mess <hostel> -<day>`")
    
    if message.content.lower().startswith('?yt'):
        if message.author.voice == None:
            await message.reply("Please connect to a voice channel")
            return
        try:
            token = utils.yt(str(message.author.voice.channel.id), os.getenv('BOT_TOKEN'))
            await message.reply(token)
        except BaseException as err:
            await message.reply(f"`{err}`")

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
                try:
                    channel = message.guild.get_channel(c)
                    await message.reply(f"Tracking mail to `{to}` on <#{str(channel.id)}>")
                    await chat.checkmail(channel, to)
                except:
                    await message.reply(f"Cannot track to `{to}` on `{c}`")
        else:
            await message.reply("Only server managers can use this command")
    
    if message.content.lower().startswith("?download"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            command = message.content.split()
            for file in command[1:]:
                try:
                    await message.reply(file= discord.File(file))
                except:
                    await message.reply(f"Could not send `{file}`")
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?upload"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            for file in message.attachments:
                try:
                    with open(file.filename, 'wb') as f:
                        await file.save(f)
                except:
                    await message.reply(f"Could not save `{file}`")
        else:
            await message.reply("Only server managers can use this command")
    
    if message.content.lower().startswith("?update"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            fname = f"logs/log-{datetime.datetime.now().isoformat()}.txt"
            await chat.update(message, open(fname, 'w'))
            await message.reply(file= discord.File(fname))
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
