# -*- coding: utf-8 -*-
import asyncio
import random
import re
from telethon.sync import TelegramClient, events
from tqdm import tqdm

api_id = '28400734'
api_hash = '9db8ca267f73280bac4672dbb60d16ea'
phone_number = '+917069804816'

file_path = 'data.txt'
group_usernames = ['alterchkbot']
approved_messages = set()
client = TelegramClient('session_name', api_id, api_hash)
cmd_file = 'cmds.txt'

# Flags to control sending
send_cards_flag = True
authorized_user_id = '6303436440'  # Replace 'your_user_id' with your actual user ID

def read_commands():
    with open(cmd_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            cmd_val = lines[0].split('=')[1].strip()
    return cmd_val

async def update_cmd(cmd_val):
    data = f"cmd = {cmd_val}"
    with open(cmd_file, 'w') as file:
        file.write(data)

# Function to read data from the text file
def read_data():
    with open(file_path, 'r') as file:
        data = file.readlines()
        bin_val = data[0].split('=')[1].strip()
        exp_m_val = data[1].split('=')[1].strip()
        exp_y_val = data[2].split('=')[1].strip()
    return bin_val, exp_m_val, exp_y_val

# Function to update data in the text file
async def update_data(bin_val, exp_m_val, exp_y_val):
    data = f"bin = {bin_val}\nexpm = {exp_m_val}\nexpy = {exp_y_val}"
    with open(file_path, 'w') as file:
        file.write(data)

# Function to generate a card with provided BIN, expiry month, and expiry year, and random CVV
def gen_card(cmd, bin_val, exp_m_val, exp_y_val):
    cvv = str(random.randint(0, 999)).zfill(3)
    card_number = bin_val
    for _ in range(15 - len(bin_val)):
        digit = random.randint(0, 9)
        card_number += str(digit)
    digits = [int(x) for x in card_number]
    for i in range(0, 16, 2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10
    card_number += str(check_digit)

    return f".{cmd} {card_number}|{exp_m_val}|{exp_y_val}|{cvv}"

async def send_message(client, group_username, card_info):
    await client.send_message(group_username, card_info)

cards_sent_count = 0

async def send_cards():
    global send_cards_flag, cards_sent_count
    while True:
        if send_cards_flag:
            bin_val, exp_m_val, exp_y_val = read_data()
            cmd = read_commands()
            card_info = gen_card(cmd, bin_val, exp_m_val, exp_y_val)
            for group_username in group_usernames:
                await send_message(client, group_username, card_info)
                cards_sent_count += 1

                # Random interval between 50 to 160 seconds
                random_interval = random.randint(35, 60)
                print(f"Waiting for {random_interval} seconds before next card...")
                for _ in tqdm(range(random_interval), desc="Waiting", unit="s"):
                    await asyncio.sleep(1)

                # Rest for 3 minutes after sending every 15 cc
                if cards_sent_count % 15 == 0:
                    print("Taking a 3-minute break...")
                    for _ in tqdm(range(180), desc="Break", unit="s"):
                        await asyncio.sleep(1)

        # Calculate remaining time to reach total delay of 37 seconds
        remaining_delay = 37 - random_interval - 180 if cards_sent_count % 15 == 0 else 37 - random_interval

        # Ensure remaining delay is non-negative
        if remaining_delay > 0:
            for _ in tqdm(range(remaining_delay), desc="Remaining Delay", unit="s"):
                await asyncio.sleep(1)
        else:
            print("No remaining delay, proceeding immediately.")

        # Adjust the remaining delay based on the condition
        await asyncio.sleep(remaining_delay if remaining_delay > 0 else 0)

@client.on(events.NewMessage(pattern=r'^/cmd'))
async def handle_cmd_update(event):
    try:
        sender_id = event.sender_id
        if sender_id == int(authorized_user_id):
            message = event.message.text
            parts = message.split()
            if len(parts) == 2 and parts[0] == '/cmd':
                new_cmd = parts[1]
                await update_cmd(new_cmd)
                await event.respond('Command updated successfully!')
    except ValueError:
        pass

@client.on(events.NewMessage(pattern=r'^/u'))
async def handle_update(event):
    try:
        sender_id = event.sender_id
        if sender_id == int(authorized_user_id):
            message = event.message.text
            if '|' in message:
                pattern = re.compile(r'/u (\d{16})\|(\d{2})\|(\d{4})')
                match = pattern.match(message)
                if match:
                    cc_number, exp_m_val, exp_y_val = match.groups()
                    bin_val = cc_number[:12]
                    await update_data(bin_val, exp_m_val, exp_y_val)
                    await event.respond('Data updated successfully!')
                else:
                    await event.respond('Invalid command format. Use "/u {cc}|{expm}|{expy}|{cvv}"')
            else:
                parts = message.split()
                if len(parts) >= 4 and parts[0] == '/u':
                    bin_val, exp_m_val, exp_y_val = parts[1], parts[2], parts[3]
                    await update_data(bin_val, exp_m_val, exp_y_val)
                    await event.respond('Data updated successfully!')
                else:
                    await event.respond('Invalid command format. Use "/u {cc}|{expm}|{expy}|{cvv}"')
    except ValueError:
        pass

@client.on(events.NewMessage(pattern=r'^/start(\s+\d+)?'))
async def handle_start(event):
    global send_cards_flag

    argument = event.pattern_match.group(1)

    if argument is None:
        if event.sender_id == int(authorized_user_id):
            send_cards_flag = True
            await event.respond('Sending cc!')
    else:
        try:
            repeat_count = int(argument.strip())
            if event.sender_id == int(authorized_user_id):
                for _ in range(repeat_count):
                    bin_val, exp_m_val, exp_y_val = read_data()
                    card_info = gen_card(cmd, bin_val, exp_m_val, exp_y_val)
                    for group_username in group_usernames:
                        await send_message(client, group_username, card_info)
                    await asyncio.sleep(45)
                send_cards_flag = False
        except ValueError:
            pass

@client.on(events.NewMessage(pattern=r'^/stop'))
async def handle_stop(event):
    global send_cards_flag
    if event.sender_id == int(authorized_user_id):
        send_cards_flag = False

@client.on(events.NewMessage(from_users=['shivxngupdbot']))
async def handle_bot_message(event):
    try:
        message = event.message.text
        pattern = re.compile(r'\.gen (\d{12}) (\d{2}) (\d{4})')
        match = pattern.match(message)
        if match:
            bin_val, exp_m_val, exp_y_val = match.groups()
            await update_data(bin_val, exp_m_val, exp_y_val)
            await event.respond('Data updated successfully from bot message!')
    except ValueError:
        pass

@client.on(events.MessageEdited(incoming=True))
async def forward_approved_messages(event):
    sender = await event.get_sender()

    if sender.username == 'alterchkbot' and event.is_private:
        if 'APPROVED' in event.message.text:
            if event.id not in approved_messages:
                print("Message contains 'approved'. Forwarding...")
                target_username = 'livinghumanoid'
                target_entity = await client.get_entity(target_username)
                await client.forward_messages(target_entity, event.message)
                approved_messages.add(event.id)
            else:
                print("Message already forwarded. Not forwarding again.")
        else:
            print("Message does not contain 'APPROVED'. Not forwarding.")

# Start the client and tasks
client.start()
client.loop.create_task(send_cards())
client.run_until_disconnected()
