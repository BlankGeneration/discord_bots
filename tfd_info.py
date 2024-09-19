import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BASE_URL = 'https://open.api.nexon.com'

HEADERS = {
    "x-nxopen-api-key": API_KEY
}

USERNAME_ALIASES = {
    'SOAD': 'SOAD__#5203',
    'BlankGeneration': 'BlankGeneration#1623'
}

async def get_metadata(endpoint):
    url = BASE_URL + endpoint
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch metadata. Status code: {response.status}, URL: {url}")
    return None

async def get_weapon_metadata():
    return await get_metadata("/static/tfd/meta/en/weapon.json")

async def get_module_metadata():
    return await get_metadata("/static/tfd/meta/en/module.json")

async def get_descendant_metadata():
    return await get_metadata("/static/tfd/meta/en/descendant.json")

async def get_ouid(username):
    url = f"{BASE_URL}/tfd/v1/id?user_name={username.replace('#', '%23')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch OUID. Status code: {response.status}, URL: {url}")
    return None

async def get_descendant_info(ouid):
    url = f"{BASE_URL}/tfd/v1/user/descendant"
    params = {"ouid": ouid}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch descendant info. Status code: {response.status}, URL: {url}")
    return None

async def get_weapon_info(ouid):
    url = f"{BASE_URL}/tfd/v1/user/weapon"
    params = {"language_code": "en", "ouid": ouid}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch weapon info. Status code: {response.status}, URL: {url}")
    return None

@bot.command()
async def descendant(ctx, username):
    full_username = USERNAME_ALIASES.get(username, username)
    ouid_response = await get_ouid(full_username)
    
    if ouid_response:
        ouid = ouid_response.get('ouid')
        if ouid:
            descendant_info = await get_descendant_info(ouid)
            descendant_metadata = await get_descendant_metadata()
            module_metadata = await get_module_metadata()
            
            if descendant_info and descendant_metadata and module_metadata:
                # Constructing the output message
                message = f"**Equipped Descendant for {full_username}**\n"
                
                # Descendant info
                descendant_name = next((item['descendant_name'] for item in descendant_metadata if item['descendant_id'] == descendant_info.get('descendant_id')), 'Unknown')
                descendant_level = descendant_info.get('descendant_level', 'N/A')
                image_url = descendant_info.get('descendant_image_url', 'No Image')
                message += f"   {descendant_name} ({descendant_level})\n"
                message += "\n"

                
                # Modules
                message += f"**Descendant Modules:**\n"
                for module in descendant_info.get('module', []):
                    module_id = module.get('module_id')
                    module_level = module.get('module_enchant_level')
                    module_details = next((item for item in module_metadata if item['module_id'] == module_id), None)
                    
                    if module_details:
                        module_name = module_details.get('module_name', 'Unknown Module')
                        socket_type = module_details.get('module_socket_type', 'N/A')
                        # Use only the first letter of the socket type
                        socket_type_initial = socket_type[0] if socket_type != 'N/A' else 'N/A'
                        message += f"   {module_name} ({module_level})({socket_type_initial})\n"
                
                # Sending the message
                max_length = 2000
                for i in range(0, len(message), max_length):
                    await ctx.send(message[i:i + max_length])
                
            else:
                await ctx.send(f"Could not find descendant information for player '{full_username}'.")
        else:
            await ctx.send(f"Could not find OUID for player '{full_username}'.")
    else:
        await ctx.send(f"Could not retrieve OUID for player '{full_username}'.")

@bot.command()
async def weapons(ctx, username):
    full_username = USERNAME_ALIASES.get(username, username)
    ouid_response = await get_ouid(full_username)
    
    if ouid_response:
        ouid = ouid_response.get('ouid')
        if ouid:
            weapon_info = await get_weapon_info(ouid)
            
            if weapon_info:
                weapon_metadata = await get_weapon_metadata()
                module_metadata = await get_module_metadata()
                
                message = f"**Weapons for {full_username}**\n\n"
                
                for weapon in weapon_info.get('weapon', []):
                    weapon_id = weapon.get('weapon_id')
                    weapon_details = next((item for item in weapon_metadata if item['weapon_id'] == weapon_id), None)
                    
                    if weapon_details:
                        weapon_name = weapon_details.get('weapon_name', 'Unknown Weapon Name')
                        weapon_type = weapon_details.get('weapon_type', 'N/A')
                        rounds = weapon_details.get('weapon_rounds_type', 'N/A')
                        enchantment_level = weapon.get('perk_ability_enchant_level', 'N/A')

                        message += f"**Weapon Name**: {weapon_name}\n"
                        message += f"**Type**: {weapon_type}\n"
                        message += f"**Rounds**: {rounds}\n"
                        message += f"**Enchantment Level**: {enchantment_level}\n"
                        message += "\n"
                        
                        # Additional Stats
                        message += f"**Additional Stats**:\n"
                        for stat in weapon.get('weapon_additional_stat', []):
                            stat_name = stat.get('additional_stat_name', 'N/A')
                            stat_value = stat.get('additional_stat_value', 'N/A')
                            message += f"  {stat_name}: {stat_value}\n"

                        # Modules
                        message += f"\n**Modules**:\n"
                        for module in weapon.get('module', []):
                            module_id = module.get('module_id')
                            module_level = module.get('module_enchant_level')
                            module_details = next((item for item in module_metadata if item['module_id'] == module_id), None)

                            # Ensure the message update is inside the loop for each module
                            if module_details:
                                socket_type = module_details.get('module_socket_type', 'N/A')
                                # Use only the first letter of the socket type
                                socket_type_initial = socket_type[0] if socket_type != 'N/A' else 'N/A'
                                message += f"   {module_details['module_name']} ({module_level})({socket_type_initial})\n"

                        message += "\n"        
                                        
                # Sending the message
                max_length = 2000
                for i in range(0, len(message), max_length):
                    await ctx.send(message[i:i + max_length])
                
            else:
                await ctx.send(f"Could not find weapon information for player '{full_username}'.")
        else:
            await ctx.send(f"Could not find OUID for player '{full_username}'.")
    else:
        await ctx.send(f"Could not retrieve OUID for player '{full_username}'.")

@bot.command()
async def tfd_help(ctx):
    help_message = (
        "`!descendant USERNAME`\n"
        "   #Fetches and displays detailed information about the equipped descendant for the given username.\n\n"
        "`!weapons USERNAME`\n"
        "   #Fetches and displays detailed information about the equipped weapons for the given username.\n"
    )
    
    # Split message if it's too long
    max_length = 2000
    for i in range(0, len(help_message), max_length):
        await ctx.send(help_message[i:i + max_length])

bot.run(DISCORD_TOKEN)
