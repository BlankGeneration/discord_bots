import discord
from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv
import math

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
    'USERNAME': 'username#5203'
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

async def get_reactor_metadata():
    return await get_metadata("/static/tfd/meta/en/reactor.json")

async def get_external_component_metadata():
    return await get_metadata("/static/tfd/meta/en/external-component.json")

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

async def get_reactor_info(ouid):
    url = f"{BASE_URL}/tfd/v1/user/reactor"
    params = {"language_code": "en", "ouid": ouid}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to fetch weapon info. Status code: {response.status}, URL: {url}")
    return None

async def get_external_component_info(ouid):
    url = f"{BASE_URL}/tfd/v1/user/external-component"
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
            reactor_info = await get_reactor_info(ouid)
            reactor_metadata = await get_reactor_metadata()
            external_component_info = await get_external_component_info(ouid)
            external_component_metadata = await get_external_component_metadata()

            if all([descendant_info, descendant_metadata, module_metadata, reactor_info, reactor_metadata, external_component_info, external_component_metadata]):
                # Constructing the output message
                message = f"**Equipped Descendant for {full_username}**\n"

                # Descendant info
                descendant_name = next((item['descendant_name'] for item in descendant_metadata if item['descendant_id'] == descendant_info.get('descendant_id')), 'Unknown')
                descendant_level = descendant_info.get('descendant_level', 'N/A')
                message += f"   {descendant_name} ({descendant_level})\n\n"

                # Modules
                message += f"**Descendant Modules:**\n"
                applied_module_stats = {}

                for module in descendant_info.get('module', []):
                    module_id = module.get('module_id')
                    module_level = module.get('module_enchant_level')
                    module_details = next((item for item in module_metadata if item['module_id'] == module_id), None)

                    if module_details:
                        module_name = module_details.get('module_name', 'Unknown Module')
                        socket_type = module_details.get('module_socket_type', 'N/A')
                        socket_type_initial = socket_type[0] if socket_type != 'N/A' else 'N/A'
                        message += f"   {module_name} ({module_level})({socket_type_initial})\n"

                        # Parsing module stats
                        module_stats = module_details.get('module_stat', [])
                        for stat in module_stats:
                            if stat['level'] == module_level:
                                stat_values = stat['value'].split(", ")
                                for stat_value in stat_values:
                                    parts = stat_value.rsplit(" ", 1)
                                    if len(parts) != 2:
                                        continue
                                    stat_name = parts[0]
                                    stat_amount = parts[1].replace('%', '')

                                    try:
                                        stat_amount = float(stat_amount)
                                    except ValueError:
                                        continue

                                    if stat_name in applied_module_stats:
                                        applied_module_stats[stat_name] += stat_amount
                                    else:
                                        applied_module_stats[stat_name] = stat_amount

                # Applied Module Stats
                message += f"\n**Applied Module Stats:**\n"
                for stat_name, stat_value in applied_module_stats.items():
                    stat_sign = "+" if stat_value > 0 else ""
                    stat_value = math.floor(stat_value * 10) / 10  # Rounding down to one decimal place
                    message += f"  {stat_name}: {stat_sign}{stat_value}%\n"

                # Reactor Information
                reactor_id = reactor_info.get('reactor_id')
                reactor_details = next((item for item in reactor_metadata if item['reactor_id'] == reactor_id), None)

                if reactor_details:
                    reactor_name = reactor_details.get('reactor_name', 'Unknown Reactor')
                    optimized_condition_type = reactor_details.get('optimized_condition_type', 'N/A')

                    message += f"\n**Reactor Information:**\n"
                    message += f"  {reactor_name}\n"
                    message += f"  Optimized Condition Type: {optimized_condition_type}\n"

                    # Reactor additional stats
                    for stat in reactor_info.get('reactor_additional_stat', []):
                        stat_name = stat.get('additional_stat_name', 'Unknown Stat')
                        stat_value = stat.get('additional_stat_value', '0.0')

                        try:
                            stat_value = float(stat_value)
                            stat_value = math.floor(stat_value * 1000) / 1000  # Rounding down to three decimal places
                            # If value has .000, display as an integer
                            if stat_value.is_integer():
                                stat_value = int(stat_value)
                        except ValueError:
                            continue

                        stat_sign = "+" if stat_value > 0 else ""
                        message += f"  {stat_name}: {stat_sign}{stat_value}\n"

                # External Components
                message += f"\n**External Components:**\n"
                for component in external_component_info.get('external_component', []):
                    component_id = component.get('external_component_id')
                    component_details = next((item for item in external_component_metadata if item['external_component_id'] == component_id), None)

                    if component_details:
                        component_name = component_details.get('external_component_name', 'Unknown Component')
                        message += f"  {component_name}\n"

                        for stat in component.get('external_component_additional_stat', []):
                            stat_name = stat['additional_stat_name']
                            stat_value = float(stat['additional_stat_value'])

                            # If the stat_value is an integer after rounding, display without decimals
                            if stat_value.is_integer():
                                stat_value = int(stat_value)
                                message += f"    {stat_name}: {stat_value}\n"
                            else:
                                # Keep 3 decimal places for non-integer values
                                message += f"    {stat_name}: {stat_value:.3f}\n"

                        message += "\n"

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

                            # Convert stat_value to float and apply rounding/formatting
                            try:
                                stat_value_float = float(stat_value)
                                # If the value is a whole number, display as an integer
                                if stat_value_float.is_integer():
                                    stat_value_display = f"{int(stat_value_float)}"
                                else:
                                    # Otherwise, show one decimal place
                                    stat_value_display = f"{stat_value_float:.1f}"
                            except ValueError:
                                stat_value_display = stat_value  # In case parsing fails, leave it as is

                            message += f"  {stat_name}: {stat_value_display}\n"

                        # Modules
                        message += f"\n**Modules**:\n"
                        for module in weapon.get('module', []):
                            module_id = module.get('module_id')
                            module_level = module.get('module_enchant_level')
                            module_details = next((item for item in module_metadata if item['module_id'] == module_id), None)

                            if module_details:
                                socket_type = module_details.get('module_socket_type', 'N/A')
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
