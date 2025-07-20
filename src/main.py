from openai import OpenAI
import os
import logging
import discord

logging.basicConfig(level=logging.INFO)
OPENAI_KEY = str(os.getenv("OPENAI_KEY"))
DISCORD_BOT_TOKEN = str(os.getenv("DISCORD_BOT_TOKEN"))

ai_client = OpenAI(
    base_url="https://api.openai.com/v1",
    api_key=OPENAI_KEY,
)

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)
reply_command_aliases = [
    "!chat",
    "!c",
    "!chatbot",
    "!cb",
    "!bot",
    "!b",
    "!ai",
    "!чат",
    "!ч",
]
clear_history_command = "!clear"
initial_prompt = ""

chat_history = {} # key: channel_id, value: list of messages

def load_initial_prompt():
    # load initial prompt from prompt.txt
    # if prompt.txt is not found, use empty initial prompt
    global initial_prompt
    try:
        with open("prompt.txt", "r", encoding="utf-8") as file:
            initial_prompt = file.read()
            logging.info("Initial prompt loaded: %s", initial_prompt)
    except FileNotFoundError:
        logging.warning("prompt.txt not found, using empty initial prompt")
        initial_prompt = ""

def clear_history(channel_id: int):
    # clear history for a specific channel
    # if channel_id is not in chat_history, do nothing
    if channel_id in chat_history:
        chat_history[channel_id] = [
            {"role": "system", "content": initial_prompt},
        ]
        
async def reply_to_message(message: discord.Message, command_used: str | None):
    # reply to a message
    # if command_used is not None, remove the command from the message
    # if message is a reply to the bot, reply to the message
    # if message is a command, reply to the message
    # if message is a normal message, reply to the message
    
    async with message.channel.typing():
        user_message = message.content.replace(command_used, "").strip() if command_used else message.content
        
        channel_id = message.channel.id
        
        if channel_id not in chat_history:
            chat_history[channel_id] = [
                {"role": "system", "content": initial_prompt},
            ]
        
        chat_history[channel_id].append({"role": "user", "content": user_message})
        
        try:
            response = ai_client.chat.completions.create(
                model="gpt-4o",  # Updated model name
                messages=chat_history[channel_id][-20:],
            )
            
            reply = response.choices[0].message.content
            chat_history[channel_id].append({"role": "assistant", "content": reply})
            
            await message.channel.send(reply, reference=message)
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            await message.channel.send("Sorry, I'm having trouble connecting to my AI service right now. Please try again later.", reference=message)

@discord_client.event
async def on_ready():
    # load initial prompt from prompt.txt
    load_initial_prompt()
    logging.info("Logged in as %s", discord_client.user)

@discord_client.event
async def on_message(message: discord.Message):
    # on message event
    # if message is from the bot, do nothing
    # if message is a command, reply to the message
    # if message is a normal message, reply to the message
    
    if message.author == discord_client.user:
        return
    logging.info("Message received: author: %s, content: %s", message.author, message.content)
    
    # check if message is command
    command_used = None
    for alias in reply_command_aliases:
        if message.content.startswith(alias):
            command_used = alias
            break
    
    # check if message is reply to bot
    is_reply_to_bot = False
    if (message.reference and 
        message.reference.message_id and    
        discord_client.user and 
        message.reference.resolved):
        try:
            is_reply_to_bot = message.reference.resolved.author == discord_client.user
        except AttributeError:
            # Referenced message might be deleted
            pass
        
    # reply to message
    if command_used or (discord_client.user and discord_client.user.mentioned_in(message)) or is_reply_to_bot:
        await reply_to_message(message, command_used)
        
    # clear history
    if message.content == clear_history_command:
        clear_history(message.channel.id)
        await message.channel.send("[History cleared for this channel]", reference=message)
        return
        
discord_client.run(DISCORD_BOT_TOKEN)