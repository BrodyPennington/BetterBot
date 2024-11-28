import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import datetime
import requests


def load_env_file(file_path=".env"):
    """Manually load environment variables from a .env file."""
    try:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"{file_path} file not found.")
    

# Load the .env file
load_env_file()

# Access environment variables
bot_token = os.getenv("DISCORD_TOKEN")
open_weather_token = os.getenv("OPEN_WEATHER")


# Define the bot's prefix and intents
intents = discord.Intents.default()
intents.message_content = True  # Ensure this intent is enabled

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()  # Sync all slash commands
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

#ban
@bot.tree.command(name="ban", description="Ban a user for a specific time with a reason.")
@app_commands.describe(
    user="The user to ban",
    duration="Ban duration in seconds",
    reason="Reason for the ban",
    notify="Whether or not notify the user of the ban"
)
async def ban(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided", notify: str = "yes"):
    # Notify the user being banned
    if notify.lower() == "yes":
        try:
            await user.send(f"You have been banned from {interaction.guild.name} for {duration} seconds. Reason: {reason}")
        except:
            await interaction.response.send_message(f"Could not DM {user.mention} about the ban.", ephemeral=True)

    # Ban the user
    await interaction.guild.ban(user, reason=reason)
    await interaction.response.send_message(f"{user.mention} has been exiled for {duration} seconds. Reason: {reason}")

    # Log the ban in a channel named #log
    log_channel = discord.utils.get(interaction.guild.channels, name="log")
    if log_channel:
        await log_channel.send(
            f"**User Banned:** {user}\n"
            f"**Duration:** {duration} seconds\n"
            f"**Reason:** {reason}\n"
            f"**Banned By:** {interaction.user.mention}"
        )
    else:
        await interaction.channel.send("Log channel not found! Please create a channel named `log`.")

    # Unban the user after the duration
    await asyncio.sleep(duration)
    await interaction.guild.unban(user)
    if log_channel:
        await log_channel.send(f"{user.mention} has been unbanned after serving their ban.")

# timeout
@bot.tree.command(name="timeout", description="Place a user in timeout for a specified duration.")
@app_commands.describe(
    user="The user to timeout",
    duration="Duration of the timeout in seconds",
    reason="Reason for the timeout",
    notify="notify the user by DM"
)
async def timeout(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided", notify: str = "no"):
    # Calculate the timeout duration
    timeout_duration = datetime.timedelta(seconds=duration)

    if notify.lower() == "yes":
        try:
            await user.send(f"You have been timed out in {interaction.guild.name} for {duration}")
        except:
            await interaction.response.send_message(f"Could not DM {user.mention} about the timeout.", ephemeral=True)

    try:
        # Place the user in timeout
        await user.timeout(timeout_duration, reason=reason)
        await interaction.response.send_message(
            f"{user.mention} has been placed in timeout for {duration} seconds. Reason: {reason}",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"I do not have permission to timeout {user.mention}.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred: {e}",
            ephemeral=True
        )

    log_channel = discord.utils.get(interaction.guild.channels, name="log")
    if log_channel:
        await log_channel.send(
            f"**User Timeout:** {user}\n"
            f"**Duration:** {duration} seconds\n"
            f"**Reason:** {reason}\n"
            f"**Timedout By:** {interaction.user.mention}"
        )
    else:
        await interaction.channel.send("Log channel not found! Please create a channel named `log`.")

# weather
def fetch_weather(city: str, state: str, api_key: str) -> str:
    """
    Fetches the weather data from OpenWeather API for a given city and state.
    """
    location = f"{city},{state},US"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        # Extract temperature
        temp = data['main']['temp']
        
        # Extract weather description
        weather_description = data['weather'][0]['description']
        
        # Check for rain
        rain_chance = "No rain expected."
        if "rain" in data:
            rain_volume = data['rain'].get("1h", 0)  # Rain volume in the last 1 hour
            rain_chance = f"Chance of rain: {rain_volume} mm in the last hour."
        elif "rain" in weather_description.lower():
            rain_chance = "Rain is expected."

        return f"The current temperature in {city}, {state} is {temp}°F.\nWeather: {weather_description.capitalize()}.\n{rain_chance}"
    
    elif response.status_code == 404:
        return f"City {city} in state {state} not found. Please check your input."
    else:
        return f"An error occurred while fetching the weather data: {response.status_code} - {response.text}"
@bot.tree.command(name="weather", description="Retrieve the weather conditions for a given city and state")
@app_commands.describe(
    city="The city where weather is being checked",
    state="The state where the city resides"
)
async def weather(interaction: discord.Interaction, city: str, state: str):
    try:
        # Call fetch_weather with the OpenWeather token
        weather_info = fetch_weather(city.strip(), state.strip(), open_weather_token)
        await interaction.response.send_message(weather_info)
    except Exception as e:
        # Handle unexpected errors gracefully
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


# Run the bot with the token from the .env file
bot.run(bot_token)
