#!/usr/bin/local/python
# -*- coding: utf-8 -*-
# Author: XuanPro, MKV mod

import asyncio
import os
import re
import sys
from asyncio.exceptions import TimeoutError
from base64 import b64encode
from contextlib import suppress
from datetime import datetime

from telethon import Button, events, functions
from telethon.errors import AlreadyInConversationError, MessageNotModifiedError

from ariabot import Aria2, bot, RPC_TOKEN, RPC_URL, USER_ID
from ariabot.util import byte2Readable, flatten_list, format_lists, format_name, getFileName, hum_convert, progress, split_list


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    if event.sender.id != USER_ID:
        await event.respond('Sorry, you do not have permission to use the Aria assistant 😢')
        return
    await hello()


@bot.on(events.NewMessage(pattern='/menu', from_users=USER_ID))
async def menu(event):
    await event.respond('Welcome to **Aria2** assistant! 👏', buttons=get_menu())


@bot.on(events.NewMessage(pattern="/close", from_users=USER_ID))
async def close(event):
    await event.respond("Keyboard closed\nSend /menu to open the keyboard", buttons=Button.clear())


@bot.on(events.NewMessage(pattern="/recon", from_users=USER_ID))
async def recon(event):
    async def dc_info():
        nonlocal DCinfo
        start = datetime.now()
        await bot(functions.PingRequest(ping_id=0))
        end = datetime.now()
        ping_duration = (end - start).microseconds / 1000
        start = datetime.now()
        DCinfo += f"\nPacket latency: `PING | {ping_duration}`"
        await msg.edit(DCinfo)
        end = datetime.now()
        msg_duration = (end - start).microseconds / 1000
        DCinfo += f"\nMessage latency: `MSG | {msg_duration}`"

    DCinfo = "**Reconnecting**"
    msg = await event.respond(DCinfo)
    await dc_info()
    await msg.edit(DCinfo)
    await bot.reconnect()
    DCinfo += "\n\n**Reconnection complete**"
    await dc_info()
    await msg.edit(DCinfo)


@bot.on(events.NewMessage(pattern="/reboot", from_users=USER_ID))
async def restart(event):
    await event.respond("Restarting Bot", buttons=Button.clear())
    python = sys.executable
    os.execv(python, ['python', '-m', 'ariabot'])


@bot.on(events.NewMessage(pattern="/help", from_users=USER_ID))
async def helper(event):
    await event.respond(
        'start - Start the program\n'
        'menu - Open the keyboard\n'
        'close - Close the keyboard\n'
        'recon - Reconnect to the network\n'
        'reboot - Restart the bot\n'
        'help - Get commands'
    )


@bot.on(events.NewMessage(from_users=USER_ID))
async def listener(event):
    text = event.raw_text
    if Aria2.client is None or Aria2.client.closed:
        await Aria2.init()
    if text == '🚀️ View Status':
        await getglobalstat(event)
        return
    elif text == '⬇ Downloading':
        await downloading(event)
        return
    elif text == '⌛ Waiting':
        await waiting(event)
        return
    elif text == '🆗 Completed/Stopped':
        await stoped(event)
        return
    elif text == '⏸ Pause Task':
        await stopTask(event)
        return
    elif text == '▶️ Start Task':
        await unstopTask(event)
        return
    elif text == '❌ Delete Task':
        await removeTask(event)
        return
    elif text == '🔁 Edit Download':
        await editTaskFile(event)
        return
    elif text == '⏸ Pause All':
        await pauseAll(event)
        return
    elif text == '▶️ Start All':
        await unpauseAll(event)
        return
    elif text == '❌ Delete All':
        await removeTaskAll(event)
        return
    elif text == '❌ Clear Completed':
        await removeAll(event)
        return
    elif text == '↩ Close Keyboard':
        await event.respond("Keyboard closed\nSend /menu to open the keyboard", buttons=Button.clear())
        return

    if 'http' in text or 'magnet' in text or 'ftp' in text:

        pat1 = re.compile(r'magnet:\?xt=urn:btih:[0-9a-fA-F]{40,}.*')
        pat2 = re.compile(r'(?:http[s]?|ftp)://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

        res1 = pat1.findall(text)
        res2 = pat2.findall(text)

        for text in (res1 + res2):
            await Aria2.client.addUri([text])

    with suppress(Exception):
        if event.media and event.media.document:
            if event.media.document.mime_type == 'application/x-bittorrent':
                await event.respond('Received a BT seed')
                path = await bot.download_media(event.message)
                await Aria2.client.add_torrent(path)
                os.remove(path)


async def hello():
    addr = re.sub(r'://|:', '/', RPC_URL.strip('/'))
    token = b64encode(RPC_TOKEN.encode('utf-8')).decode('utf-8')
    url = f"http://ariang.eu.org/#!/settings/rpc/set/{addr}/{token}"
    giturl = 'https://github.com/xuanpro/ariabot'
    await bot.send_message(
        USER_ID,
        'Welcome to **Aria2** assistant! 👏\n\n'
        'Send /start to start the program\n'
        'Send /menu to open the menu\n'
        'Send /close to close the menu\n'
        'Send /recon to reconnect to the network\n'
        'Send /reboot to restart the bot\n'
        'Send /help to get commands',
        buttons=[Button.url('🚀️AriaNg', url), Button.url('Github', giturl)])


# Text button callback methods=============================


async def getglobalstat(event):
    res = await Aria2.client.getGlobalStat()
    downloadSpeed = hum_convert(int(res['downloadSpeed']))
    uploadSpeed = hum_convert(int(res['uploadSpeed']))
    numActive = res['numActive']
    numWaiting = res['numWaiting']
    numStopped = res['numStopped'])
    info = f'Welcome to **Aria2** assistant! 👏\n\n'
    info += f'Download: `{downloadSpeed}`\n'
    info += f'Upload: `{uploadSpeed}`\n'
    info += f'Active: `{numActive}`\n'
    info += f'Waiting: `{numWaiting}`\n'
    info += f'Stopped: `{numStopped}`'
    await event.respond(info)


async def downloading(event):
    # Tasks that are downloading
    tasks = await Aria2.client.tellActive()
    if not tasks:
        await event.respond('No tasks are running')
        return
    send_str = ''
    for task in tasks:
        completedLength = task['completedLength']
        totalLength = task['totalLength']
        downloadSpeed = task['downloadSpeed']
        fileName = getFileName(task)
        if fileName == '':
            continue
        prog = progress(int(totalLength), int(completedLength))
        size = byte2Readable(int(totalLength))
        speed = hum_convert(int(downloadSpeed))
        send_str += f'Task Name: {fileName}\nProgress: {prog}\nSize: {size}\nSpeed: {speed}\n\n'
    if send_str:
        for i in range(0, len(send_str), 4000):
            await event.respond(send_str[i:i + 4000])
    else:
        await event.respond('Unable to recognize the task name, please send /start to use AriaNG to view')


async def waiting(event):
    # Tasks that are waiting
    tasks = await Aria2.client.tellWaiting(0, 1000)
    if not tasks:
        await event.respond('The task list is empty')
        return
    send_str = ''
    for task in tasks:
        completedLength = task['completedLength']
        totalLength = task['totalLength']
        downloadSpeed = task['downloadSpeed']
        fileName = getFileName(task)
        prog = progress(int(totalLength), int(completedLength))
        size = byte2Readable(int(totalLength))
        speed = hum_convert(int(downloadSpeed))
        send_str += f'Task Name: {fileName}\nProgress: {prog}\nSize: {size}\nSpeed: {speed}\n\n'
    if send_str:
        for i in range(0, len(send_str), 4000):
            await event.respond(send_str[i:i + 4000])
    else:
        await event.respond('Unable to recognize the task name, please send /start to use AriaNG to view')


async def stoped(event):
    # Completed/stopped tasks
    tasks = await Aria2.client.tellStopped(0, 1000)
    if not tasks:
        await event.respond('Task list is empty')
        return
    send_str = ''
    for task in tasks:
        completedLength = task['completedLength']
        totalLength = task['totalLength']
        downloadSpeed = task['downloadSpeed']
        fileName = getFileName(task)
        prog = progress(int(totalLength), int(completedLength))
        size = byte2Readable(int(totalLength))
        speed = hum_convert(int(downloadSpeed))
        send_str += f'Task name: {fileName}\nProgress: {prog}\nSize: {size}\nSpeed: {speed}\n\n'
    if send_str:
        for i in range(0, len(send_str), 4000):
            await event.respond(send_str[i:i + 4000])
    else:
        await event.respond('Unable to recognize task name, please send /start to use AriaNG to view')


async def unstopTask(event):
    tasks = await Aria2.client.tellWaiting(0, 1000)
    if not tasks:
        await event.respond('Task list is empty')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        buttons.append(Button.inline(format_name(fileName), task['gid']))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Please select the task to start ▶', event, buttons, conv)
            if res:
                await msg.delete()
                await Aria2.client.unpause(data)
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Cannot start multiple conversations in the same chat")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Selection timed out")


async def stopTask(event):
    tasks = await Aria2.client.tellActive()
    if not tasks:
        await event.respond('Task list is empty')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name(fileName), gid))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Please select the task to pause ⏸', event, buttons, conv)
            if res:
                await msg.delete()
                await Aria2.client.pause(data)
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Cannot start multiple conversations in the same chat")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Selection timed out")


async def removeTask(event):
    tasks1 = await Aria2.client.tellActive()
    tasks2 = await Aria2.client.tellWaiting(0, 1000)
    tasks3 = await Aria2.client.tellStopped(0, 1000)
    tasks = tasks1 + tasks2
    if not (tasks + tasks3):
        await event.respond('Task list is empty')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name(fileName), 'del->' + gid))
    for task in tasks3:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name('Ended ·' + fileName), 'result->' + gid))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Please select the task to delete ❌', event, buttons, conv)
            if res:
                mode, gid = data.split('->', 1)
                if mode == 'result':
                    await Aria2.client.removeDownloadResult(gid)
                else:
                    await Aria2.client.remove(gid)
                await bot.edit_message(msg, 'Task deleted successfully')
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Cannot start multiple conversations in the same chat")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Selection timed out")


async def editTaskFile(event):
    tasks1 = await Aria2.client.tellActive()
    tasks2 = await Aria2.client.tellWaiting(0, 1000)
    tasks = tasks1 + tasks2
    if not tasks:
        await event.respond('Task list is empty')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name(fileName), gid))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Please select the task to edit', event, buttons, conv)
            if res:
                await editToTaskFile(res, conv, data)
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Cannot start multiple conversations in the same chat")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Selection timed out")


async def removeTaskAll(event):
    tasks1 = await Aria2.client.tellActive()
    tasks2 = await Aria2.client.tellWaiting(0, 1000)
    tasks = tasks1 + tasks2
    if not tasks:
        await event.respond('Task list is empty')
        return
    for task in tasks:
        await Aria2.client.remove(task['gid'])
    await event.respond('All tasks deleted')


# Pause all tasks
async def pauseAll(event):
    await Aria2.client.pauseAll()
    await event.respond('All tasks paused')


# Start all tasks
async def unpauseAll(event):
    await Aria2.client.unpauseAll()
    await event.respond('All tasks started')


# Clear all completed/stopped tasks
async def removeAll(event):
    # Delete completed or stopped tasks
    await Aria2.client.purgeDownloadResult()
    await event.respond('Tasks cleared')


# Edit file
async def editToTaskFile(event, conv, gid):
    msg = await event.edit('Please wait, querying...')
    filesinfo = await Aria2.client.getFiles(gid)
    buttons = []
    for task in filesinfo:
        buttons.append(Button.inline(format_name(task['index'] + ':' + os.path.basename(task['path'].replace(' ', ''))), task['index']))
    size, line = 2, 10
    buttons = split_list(buttons, size)
    page = 0
    ids = []
    while True:
        btns = list(buttons)
        if len(btns) > line:
            btns = split_list(btns, line)
            my_btns = [
                Button.inline('Previous Page', data='up'),
                Button.inline(f'{page + 1}/{len(btns)}', data='jump'),
                Button.inline('Next Page', data='next')
            ]
            if page > len(btns) - 1:
                page = 0
            new_btns = btns[page]
            new_btns.append(my_btns)
        else:
            new_btns = btns
        new_btns.append([Button.inline('Select All on This Page', 'checkall'), Button.inline('Exclude Selection', 'exclude'), Button.inline('Include Selection', 'over')])
        new_btns.append(get_cancel())
        with suppress(MessageNotModifiedError):
            msg = await msg.edit('Please select the tasks to download (multiple selections allowed)' + (f"\nCurrent Selection: {format_lists(ids)}" if ids else ''), buttons=new_btns)
        res_1 = await conv.wait_event(press_event(event))
        data_1 = res_1.data.decode()
        if data_1 == 'cancel':
            await bot.edit_message(msg, 'Selection canceled')
            return
        elif data_1 == 'up':
            page -= 1
            if page < 0:
                page = len(btns) - 1
            continue
        elif data_1 == 'next':
            page += 1
            if page > len(btns) - 1:
                page = 0
            continue
        elif data_1 == 'jump':
            page_btns = [Button.inline(f'Page {i + 1} {1 + i * line * size} - {(1 + i) * line * size}', data=str(i)) for i in range(len(btns))]
            page_btns = split_list(page_btns, 3)
            page_btns.append([Button.inline('Back', data='cancel')])
            await bot.edit_message(msg, 'Please select a page to jump to', buttons=page_btns)
            res_2 = await conv.wait_event(press_event(event))
            data_2 = res_2.data.decode()
            if data_2 == 'cancel':
                continue
            else:
                page = int(data_2)
                continue
        elif data_1 == 'over':
            break
        elif data_1 == 'exclude':
            numbers = [str(i) for i in range(1, len(filesinfo) + 1)]
            ids = [i for i in numbers if i not in ids]
            break
        elif data_1 in ids:
            ids.remove(data_1)
        elif data_1 == 'checkall':
            checkall = flatten_list(new_btns)
            pageids = [id for i in checkall if (id := i.to_dict()['data'].decode()).isdigit()]
            if set(pageids).issubset(set(ids)):
                ids = list(set(ids) - set(pageids))
            else:
                ids.extend(pageids)
        else:
            ids.append(data_1)
        ids = list(set(ids))
        ids.sort(key=lambda x: int(x))
        if len(ids) == len(filesinfo):
            break
    if ids:
        msg = await bot.edit_message(msg, f"Current Selection: {format_lists(ids)}")
        args = {'select-file': ','.join(ids), 'bt-remove-unselected-file': 'true'}
        with suppress(Exception):
            await Aria2.client.changeOption(gid, args)
        await msg.edit(msg.text + '\nModification complete')
    else:
        await bot.edit_message(msg, f"Not modified")


def press_event(event):
    return events.CallbackQuery(func=lambda e: e.sender_id == event.sender.id)


def get_menu():
    return [
        [
            Button.text('🚀️ View Status'),
        ],
        [
            Button.text('⬇ Downloading'),
            Button.text('⌛ Waiting'),
            Button.text('🆗 Completed/Stopped')
        ],
        [
            Button.text('▶️ Start Task'),
            Button.text('⏸ Pause Task'),
            Button.text('❌ Delete Task'),
        ],
        [
            Button.text('▶️ Start All'),
            Button.text('⏸ Pause All'),
            Button.text('❌ Delete All')
        ],
        [
            Button.text('🔁 Modify Download'),
            Button.text('❌ Clear Completed'),
            Button.text('↩ Close Keyboard'),
        ],
    ]


def get_cancel():
    return [Button.inline('Cancel', 'cancel')]


async def get_pagesplit(text, event, buttons, conv):
    size, line = 2, 5
    buttons = split_list(buttons, size)
    page = 0
    msg = await conv.send_message(text)
    while True:
        btns = buttons
        if len(btns) > line:
            btns = split_list(btns, line)
            my_btns = [
                Button.inline('Previous Page', data='up'),
                Button.inline(f'{page + 1}/{len(btns)}', data='jump'),
                Button.inline('Next Page', data='next')
            ]
            if page > len(btns) - 1:
                page = 0
            new_btns = btns[page]
            new_btns.append(my_btns)
        else:
            new_btns = btns
        new_btns.append(get_cancel())
        await msg.edit(text, buttons=new_btns)
        res = await conv.wait_event(press_event(event))
        data = res.data.decode()
        if data == 'cancel':
            await bot.edit_message(msg, 'Selection canceled')
            return None, None, msg
        elif data == 'up':
            page -= 1
            if page < 0:
                page = len(btns) - 1
            continue
        elif data == 'next':
            page += 1
            if page > len(btns) - 1:
                page = 0
            continue
        elif data == 'jump':
            page_btns = [Button.inline(f'Page {i + 1} {1 + i * line * size} - {(1 + i) * line * size}', data=str(i)) for i in range(len(btns))]
            page_btns = split_list(page_btns, 3)
            page_btns.append([Button.inline('Back', data='cancel')])
            await bot.edit_message(msg, 'Please select a page to jump to', buttons=page_btns)
            res_2 = await conv.wait_event(press_event(event))
            data_2 = res_2.data.decode()
            if data_2 == 'cancel':
                continue
            else:
                page = int(data_2)
                continue
        else:
            return res, data, msg
