from . import utils
import datetime
import asyncio
import json
import discord

async def checkmail(channel, to, old_mails={}):
    while True:
        print("Checking for mails "+str(datetime.datetime.now()))
        new_mails = utils.fetch_circulars(to)
        for m in new_mails:
            if m not in old_mails:
                await channel.send("@everyone **"+str(m)[:150]+"**"+'\n'+str(new_mails[m])[:1800])
        await asyncio.sleep(60)
        old_mails = new_mails

async def help(message):
    message.reply(
"""
**Commands**
- `hello` to check if bot is online
- `?help` to display this message
- `?set <kerberos>` to set your kerberos and automatically assign role for branch, hostel and courses
- `?courses` (self) or `?courses <kerberos>` or `?courses @User` to list courses
- `?slot <course>` to get slot for a course
- `?tt` (self) or `?tt <kerberos>` or `?tt @User` to get yours or someone else's timetable (excluding labs for now)
- `?mess` (self)(today) or `?mess <hostel> -<day>` to get mess menu for the hostel on that day
- Works for multiple inputs too! Try `?slot COL106 COL202`

_Manager only_ -
- `?edit <kerberos> @User` to edit kerberos for some user
- `?checkmail <mail-to> #Channel` to track circular emails on that channel every minute
- `?update` to update roles for all registered users
- `?reload` to reload the database from `.csv` and `.json` files
- `?fetchldap` to fetch courses data from ldap and reload

Curious how this works? Check out the source code at https://github.com/as1605/IITD-Bot 
and leave a :star: if you like it
""")

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
            print("No role exists for `"+year+"`. Please request admin to create")

        hostel = str(utils.kerberos_lookup[kerberos]["hostel"])
        for h in utils.hostels:
            if discord.utils.get(message.guild.roles, name = h) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = h))  
        try:
            await user.add_roles(discord.utils.get(message.guild.roles, name = hostel))
        except:
            print("No role exists for `"+hostel+"`. Please request admin to create")

        branch = str(kerberos[:3]).upper()
        for b in utils.branches:
            if discord.utils.get(message.guild.roles, name = b.upper()) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = b.upper()))
        try:
            await user.add_roles(discord.utils.get(message.guild.roles, name = branch))
        except:
            print("No role exists for `"+branch+"`. Please request admin to create")

        course = utils.get_student_courses(kerberos)
        for c in utils.courses:
            if discord.utils.get(message.guild.roles, name = c) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = c))
        for c in course:
            try:
                await user.add_roles(discord.utils.get(message.guild.roles, name = c))
            except:
                print("No role exists for `"+c+"`. Please request admin to create")
        await message.reply("Successfully set kerberos!")
    else:
        await message.reply("Could not find `"+kerberos+"` in kerberos database.")


async def update(message, log):
    discord_ids = json.load(open("discord_ids.json"))
    kerb_id = {}
    async for user in message.guild.fetch_members(limit=None):
        id = str(user.id)
        if id not in discord_ids:
            if discord.utils.get(message.guild.roles, name = "Bot") not in user.roles:
                log.write("ERROR: Did not find `"+user.name+"` in discord_ids"+'\n')
            continue
        kerberos = str(discord_ids[id]['kerberos'])
        if kerberos in kerb_id:
            log.write("WARNING: DUPLICATE key `"+kerberos+"` for `"+user.name+"` and `"+discord_ids[kerb_id[kerberos]]['kerberos']+"`\n")
        else:
            kerb_id[kerberos] = id
        if kerberos in utils.kerberos_lookup:
            name = str(utils.kerberos_lookup[kerberos]["name"])
            if name != user.nick and name != user.name:
                log.write("WARNING: NICK for `"+user.name+"` expected: `"+name+"`, found: `"+str(user.nick)+"`\n")

            year = "20"+str(kerberos[3:5])
            for y in utils.years:
                if y != year and discord.utils.get(message.guild.roles, name = y) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = y))
                    log.write("ACTION: Removed role `"+y+"` for `"+user.name+"`\n")
            if discord.utils.get(message.guild.roles, name = year) not in user.roles:
                try:
                    await user.add_roles(discord.utils.get(message.guild.roles, name = year))
                    log.write("ACTION: Added role `"+year+"` for `"+user.name+"`\n")
                except:
                    pass
                    #log.write("WARNING: ROLE not found `"+year+"`"+'\n')

            hostel = str(utils.kerberos_lookup[kerberos]["hostel"])
            for h in utils.hostels:
                if h != hostel and discord.utils.get(message.guild.roles, name = h) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = h))
                    log.write("ACTION: Removed role `"+h+"` for `"+user.name+"`\n")
            if discord.utils.get(message.guild.roles, name = hostel) not in user.roles:
                try:
                    await user.add_roles(discord.utils.get(message.guild.roles, name = hostel))
                    log.write("ACTION: Added role `"+hostel+"` for `"+user.name+"`\n")
                except:
                    pass
                    #log.write("WARNING: ROLE not found `"+hostel+"`"+'\n')

            branch = str(kerberos[:3]).upper()
            for b in utils.branches:
                if b.upper() != branch and discord.utils.get(message.guild.roles, name = b.upper()) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = b.upper()))
                    log.write("ACTION: Removed role `"+b.upper()+"` for `"+user.name+"`\n")
            if discord.utils.get(message.guild.roles, name = branch) not in user.roles:
                try:
                    await user.add_roles(discord.utils.get(message.guild.roles, name = branch))
                    log.write("ACTION: Added role `"+branch+"` for `"+user.name+"`\n")
                except:
                    pass
                    #log.write("WARNING: ROLE not found `"+branch+"`"+'\n')

            course = utils.get_student_courses(kerberos)
            for c in utils.courses:
                if c not in course and discord.utils.get(message.guild.roles, name = c) in user.roles:
                    await user.remove_roles(discord.utils.get(message.guild.roles, name = c))
                    log.write("ACTION: Removed role `"+c+"` for `"+user.name+"`\n")
            for c in course:
                if discord.utils.get(message.guild.roles, name = c) not in user.roles:
                    try:
                        await user.add_roles(discord.utils.get(message.guild.roles, name = c))
                        log.write("ACTION: Added role `"+c+"` for `"+user.name+"`\n")
                    except:
                        pass
                        #log.write("WARNING: ROLE not found `"+c+"`"+'\n')
        else:
            log.write("ERROR: Could not find `"+kerberos+"` in kerberos database"+'\n')
