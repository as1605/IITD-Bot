import utils
import discord
import json
import os
from dotenv import load_dotenv
import asyncio


client = discord.Client()


async def checkmail(channel, old_mails={}):
    print("Checking for mails")
    new_mails = utils.fetch_circulars()
    for m in new_mails:
        if m not in old_mails:
            await channel.send("**"+str(m)+"**"+'\n'+str(new_mails[m])[:1900])
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
                await message.reply("**INFO:** Kerberos for "+discord_ids[id]['username']+" was previously set to `"+discord_ids[id]['kerberos']+"`")
            else:
                await message.reply("Updating details...")
        discord_ids.update({id : {'username':str(user.name), 'kerberos':str(kerberos)}})
        with open("discord_ids.json", "w") as outfile:
            json.dump(discord_ids, outfile)

        name = str(utils.kerberos_lookup[kerberos]["name"])
        try:
            await user.edit(nick = name)
        except:
            await message.reply("Insufficient permissions to change nick")

        hostel = str(utils.kerberos_lookup[kerberos]["hostel"])
        for h in utils.hostels:
            if discord.utils.get(message.guild.roles, name = h) in user.roles:
                await user.remove_roles(discord.utils.get(message.guild.roles, name = h))  
        try:
            await user.add_roles(discord.utils.get(message.guild.roles, name = hostel))
        except:
            await message.reply("No role exists for `"+hostel+"`. Please request admin to create")

        branch = kerberos[:3].upper()
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
- `?courses <kerberos>` to list courses by kerberos id
_Manager only_ -
- `?checkmail` to track circular emails on that channel every minute
- `?update` to update roles for all registered users
- `?reload` to reload the database from `.csv` and `.json` files
""")
    if message.content.lower().startswith("?courses"):
        command = message.content.lower().split(' ')
        if len(command) > 1:
            kerberos = command[1]
            courses = ' '
            for c in utils.get_student_courses(kerberos):
                courses += c + ' '
            await message.reply("You are enrolled in `"+courses+"`")
        else:
            await message.reply("Command is `?courses <kerberos>`. Try `?courses ee1200461`")

    if message.content.lower().startswith("?set"):
        command = message.content.lower().split(' ')
        if len(command) > 1:
            kerberos = command[1]
            await set(message, message.author.id, kerberos)
        else:
            await message.reply("Command is `?set <kerberos>`")

    if message.content.lower().startswith("?update"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            discord_ids = json.load(open("discord_ids.json"))
            for id in discord_ids:
                await set(message, id, discord_ids[id]['kerberos'])
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?reload"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            utils.reload()
            await message.reply("Reloaded database")
        else:
            await message.reply("Only server managers can use this command")

    if message.content.lower().startswith("?checkmail"):
        if discord.utils.get(message.guild.roles, name = "Manager") in message.author.roles:
            await message.channel.send("Tracking mail on <#"+str(message.channel.id)+">")
            await checkmail(message.channel)
        else:
            await message.reply("Only server managers can use this command")


utils.reload()
load_dotenv()
client.run(os.getenv('BOT_TOKEN'))