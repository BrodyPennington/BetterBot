import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import datetime
import openai

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
openai.api_key = os.getenv("OPENAI_TOKEN")

# Define the bot's prefix and intents
intents = discord.Intents.default()
intents.message_content = True  # Ensure this intent is enabled

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()  # Sync all slash commands
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="ban", description="Ban a user for a specific time with a reason.")
@app_commands.describe(
    user="The user to ban",
    duration="Ban duration in seconds",
    reason="Reason for the ban"
)

async def ban(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
    # Notify the user being banned
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





@bot.tree.command(name="timeout", description="Place a user in timeout for a specified duration.")

@app_commands.describe(
    user="The user to timeout",
    duration="Duration of the timeout in seconds",
    reason="Reason for the timeout"
)

async def timeout(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
    # Calculate the timeout duration
    timeout_duration = datetime.timedelta(seconds=duration)
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

@bot.tree.command(name="chat", description="Chat with OpenAI GPT.")
@app_commands.describe(message="Your message to the AI.")
async def chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()  # Acknowledge the interaction
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ]
        )
        reply = response['choices'][0]['message']['content']
        await interaction.followup.send(reply)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")



# Run the bot with the token from the .env file
bot.run(bot_token)
