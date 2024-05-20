#!/usr/bin/local/python
# -*- coding: utf-8 -*-
# Author: XuanPro

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
        await event.respond('Maaf, Anda tidak memiliki izin untuk menggunakan Asisten Aria 😢')
        return
    await hello()


@bot.on(events.NewMessage(pattern='/menu', from_users=USER_ID))
async def menu(event):
    await event.respond('Selamat datang di **Asisten Aria2**! 👏', buttons=get_menu())


@bot.on(events.NewMessage(pattern="/close", from_users=USER_ID))
async def close(event):
    await event.respond("Keyboard ditutup\nKirim /menu untuk membuka keyboard", buttons=Button.clear())


@bot.on(events.NewMessage(pattern="/recon", from_users=USER_ID))
async def recon(event):
    async def dc_info():
        nonlocal DCinfo
        start = datetime.now()
        await bot(functions.PingRequest(ping_id=0))
        end = datetime.now()
        ping_duration = (end - start).microseconds / 1000
        start = datetime.now()
        DCinfo += f"\nLambat Ping: `PING | {ping_duration}`"
        await msg.edit(DCinfo)
        end = datetime.now()
        msg_duration = (end - start).microseconds / 1000
        DCinfo += f"\nLambat Pesan:   `MSG | {msg_duration}`"

    DCinfo = "**Menghubungkan kembali**"
    msg = await event.respond(DCinfo)
    await dc_info()
    await msg.edit(DCinfo)
    await bot.reconnect()
    DCinfo += "\n\n**Menghubungkan kembali selesai**"
    await dc_info()
    await msg.edit(DCinfo)


@bot.on(events.NewMessage(pattern="/reboot", from_users=USER_ID))
async def restart(event):
    await event.respond("Bot sedang direstart", buttons=Button.clear())
    python = sys.executable
    os.execv(python, ['python', '-m', 'ariabot'])


@bot.on(events.NewMessage(pattern="/help", from_users=USER_ID))
async def helper(event):
    await event.respond(
        'start-Memulai program\n'
        'menu-Membuka keyboard\n'
        'close-Menutup keyboard\n'
        'recon-Menghubungkan kembali jaringan\n'
        'reboot-Memulai ulang bot\n'
        'help-Mendapatkan perintah'
    )


@bot.on(events.NewMessage(from_users=USER_ID))
async def lisenter(event):
    text = event.raw_text
    if Aria2.client is None or Aria2.client.closed:
        await Aria2.init()
    if text == '🚀️ Lihat Status':
        await getglobalstat(event)
        return
    elif text == '⬇ Sedang Mendownload':
        await downloading(event)
        return
    elif text == '⌛ Sedang Menunggu':
        await waiting(event)
        return
    elif text == '🆗 Selesai/Dihentikan':
        await stoped(event)
        return
    elif text == '⏸ Jeda Tugas':
        await stopTask(event)
        return
    elif text == '▶️ Mulai Tugas':
        await unstopTask(event)
        return
    elif text == '❌ Hapus Tugas':
        await removeTask(event)
        return
    elif text == '🔁 Ubah Download':
        await editTaskFile(event)
        return
    elif text == '⏸ Jeda Semua':
        await pauseAll(event)
        return
    elif text == '▶️ Mulai Semua':
        await unpauseAll(event)
        return
    elif text == '❌ Hapus Semua':
        await removeTaskAll(event)
        return
    elif text == '❌ Hapus Selesai':
        await removeAll(event)
        return
    elif text == '↩ Tutup Keyboard':
        await event.respond("Keyboard ditutup\nKirim /menu untuk membuka keyboard", buttons=Button.clear())
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
                await event.respond('Menerima sebuah file torrent')
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
        'Selamat datang di **Asisten Aria2**! 👏\n\n'
        'Kirim /start untuk memulai program\n'
        'Kirim /menu untuk membuka menu\n'
        'Kirim /close untuk menutup menu\n'
        'Kirim /recon untuk menghubungkan kembali jaringan\n'
        'Kirim /reboot untuk memulai ulang bot\n'
        'Kirim /help untuk mendapatkan perintah',
        buttons=[Button.url('🚀️AriaNg', url), Button.url('Github', giturl)])


# Metode Kembali Panggilan Tombol Teks=============================


async def getglobalstat(event):
    res = await Aria2.client.getGlobalStat()
    downloadSpeed = hum_convert(int(res['downloadSpeed']))
    uploadSpeed = hum_convert(int(res['uploadSpeed']))
    numActive = res['numActive']
    numWaiting = res['numWaiting']
    numStopped = res['numStopped']
    info = f'Selamat datang di **Asisten Aria2**! 👏\n\n'
    info += f'Download: `{downloadSpeed}`\n'
    info += f'Upload: `{uploadSpeed}`\n'
    info += f'Sedang mengunduh: `{numActive}`\n'
    info += f'Sedang menunggu: `{numWaiting}`\n'
    info += f'Selesai/Dihentikan: `{numStopped}`'
    await event.respond(info)


async def downloading(event):
    # Tugas yang sedang diunduh
    tasks = await Aria2.client.tellActive()
    if not tasks:
        await event.respond('Tidak ada tugas yang sedang berjalan')
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
        send_str += f'Nama Tugas: {fileName}\nProgress: {prog}\nUkuran: {size}\nKecepatan: {speed}\n\n'
    if send_str:
        for i in range(0, len(send_str), 4000):
            await event.respond(send_str[i:i + 4000])
    else:
        await event.respond('Tidak dapat mengenali nama tugas, kirim /start untuk menggunakan AriaNG')

async def waiting(event):
    # Tugas yang sedang menunggu
    tasks = await Aria2.client.tellWaiting(0, 1000)
    if not tasks:
        await event.respond('Daftar tugas kosong')
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
        send_str += f'Nama Tugas: {fileName}\nProgress: {prog}\nUkuran: {size}\nKecepatan: {speed}\n\n'
    if send_str:
        for i in range(0, len(send_str), 4000):
            await event.respond(send_str[i:i + 4000])
    else:
        await event.respond('Tidak dapat mengenali nama tugas, kirim /start untuk menggunakan AriaNG')


async def stoped(event):
    # Tugas yang selesai/dihentikan
    tasks = await Aria2.client.tellStopped(0, 1000)
    if not tasks:
        await event.respond('Daftar tugas kosong')
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
        send_str += f'Nama Tugas: {fileName}\nProgress: {prog}\nUkuran: {size}\nKecepatan: {speed}\n\n'
    if send_str:
        for i in range(0, len(send_str), 4000):
            await event.respond(send_str[i:i + 4000])
    else:
        await event.respond('Tidak dapat mengenali nama tugas, kirim /start untuk menggunakan AriaNG')


async def unstopTask(event):
    tasks = await Aria2.client.tellWaiting(0, 1000)
    if not tasks:
        await event.respond('Daftar tugas kosong')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        buttons.append(Button.inline(format_name(fileName), task['gid']))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Pilih tugas yang ingin dimulai▶️', event, buttons, conv)
            if res:
                await msg.delete()
                await Aria2.client.unpause(data)
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Tidak dapat memulai lebih dari satu percakapan dalam obrolan yang sama")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Waktu untuk memilih telah habis")


async def stopTask(event):
    tasks = await Aria2.client.tellActive()
    if not tasks:
        await event.respond('Daftar tugas kosong')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name(fileName), gid))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Pilih tugas yang ingin dijeda⏸', event, buttons, conv)
            if res:
                await msg.delete()
                await Aria2.client.pause(data)
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Tidak dapat memulai lebih dari satu percakapan dalam obrolan yang sama")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Waktu untuk memilih telah habis")

async def removeTask(event):
    tasks1 = await Aria2.client.tellActive()
    tasks2 = await Aria2.client.tellWaiting(0, 1000)
    tasks3 = await Aria2.client.tellStopped(0, 1000)
    tasks = tasks1 + tasks2
    if not (tasks + tasks3):
        await event.respond('Daftar tugas kosong')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name(fileName), 'del->' + gid))
    for task in tasks3:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name('Selesai·' + fileName), 'result->' + gid))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Pilih tugas yang ingin dihapus❌', event, buttons, conv)
            if res:
                mode, gid = data.split('->', 1)
                if mode == 'result':
                    await Aria2.client.removeDownloadResult(gid)
                else:
                    await Aria2.client.remove(gid)
                await bot.edit_message(msg, 'Tugas berhasil dihapus')
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Tidak dapat memulai lebih dari satu percakapan dalam obrolan yang sama")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Waktu untuk memilih telah habis")


async def editTaskFile(event):
    tasks1 = await Aria2.client.tellActive()
    tasks2 = await Aria2.client.tellWaiting(0, 1000)
    tasks = tasks1 + tasks2
    if not tasks:
        await event.respond('Daftar tugas kosong')
        return
    buttons = []
    for task in tasks:
        fileName = getFileName(task)
        gid = task['gid']
        buttons.append(Button.inline(format_name(fileName), gid))
    try:
        async with bot.conversation(event.sender.id, timeout=60) as conv:
            res, data, msg = await get_pagesplit('Pilih tugas yang ingin diubah', event, buttons, conv)
            if res:
                await editToTaskFile(res, conv, data)
    except AlreadyInConversationError:
        wait = await bot.send_message(event.sender.id, "Tidak dapat memulai lebih dari satu percakapan dalam obrolan yang sama")
        await asyncio.sleep(5)
        await wait.delete()
    except TimeoutError:
        await bot.edit_message(msg, "Waktu untuk memilih telah habis")


async def removeTaskAll(event):
    tasks1 = await Aria2.client.tellActive()
    tasks2 = await Aria2.client.tellWaiting(0, 1000)
    tasks = tasks1 + tasks2
    if not tasks:
        await event.respond('Daftar tugas kosong')
        return
    for task in tasks:
        await Aria2.client.remove(task['gid'])
    await event.respond('Menghapus semua tugas')


# Jeda semua
async def pauseAll(event):
    await Aria2.client.pauseAll()
    await event.respond('Semua tugas dijeda')


# Mulai semua
async def unpauseAll(event):
    await Aria2.client.unpauseAll()
    await event.respond('Semua tugas dimulai')


# Panggil hapus semua selesai/berhenti
async def removeAll(event):
    # Hapus selesai atau berhenti
    await Aria2.client.purgeDownloadResult()
    await event.respond('Tugas telah dihapus semua')


# Mengedit berkas
async def editToTaskFile(event, conv, gid):
    msg = await event.edit('Harap tunggu, sedang mengambil informasi...')
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
                Button.inline('Halaman Sebelumnya', data='up'),
                Button.inline(f'{page + 1}/{len(btns)}', data='jump'),
                Button.inline('Halaman Berikutnya', data='next')
            ]
            if page > len(btns) - 1:
                page = 0
            new_btns = btns[page]
            new_btns.append(my_btns)
        else:
            new_btns = btns
        new_btns.append([Button.inline('Pilih Semua di Halaman', 'checkall'), Button.inline('Kecuali yang Dipilih', 'exclude'), Button.inline('Sertakan yang Dipilih', 'over')])
        new_btns.append(get_cancel())
        with suppress(MessageNotModifiedError):
            msg = await msg.edit('Pilih tugas yang ingin diunduh (bisa memilih lebih dari satu)' + (f"\nPilihan saat ini: {format_lists(ids)}" if ids else ''), buttons=new_btns)
        res_1 = await conv.wait_event(press_event(event))
        data_1 = res_1.data.decode()
        if data_1 == 'cancel':
            await bot.edit_message(msg, 'Pemilihan dibatalkan')
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
            page_btns = [Button.inline(f'Halaman {i + 1} {1 + i * line * size} - {(1 + i) * line * size}', data=str(i)) for i in range(len(btns))]
            page_btns = split_list(page_btns, 3)
            page_btns.append([Button.inline('Kembali', data='cancel')])
            await bot.edit_message(msg, 'Pilih halaman untuk melompat', buttons=page_btns)
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
        msg = await bot.edit_message(msg, f"Seleksi saat ini: {format_lists(ids)}")
        args = {'select-file': ','.join(ids), 'bt-remove-unselected-file': 'true'}
        with suppress(Exception):
            await Aria2.client.changeOption(gid, args)
        await msg.edit(msg.text + '\nPenyuntingan selesai')
    else:
        await bot.edit_message(msg, f"Tidak ada penyuntingan yang dilakukan")


def press_event(event):
    return events.CallbackQuery(func=lambda e: e.sender_id == event.sender.id)


def get_menu():
    return [
        [
            Button.text('🚀️ Lihat Status'),
        ],
        [
            Button.text('⬇ Sedang Mendownload'),
            Button.text('⌛ Sedang Menunggu'),
            Button.text('🆗 Sudah Selesai/Stop')
        ],
        [
            Button.text('▶️ Mulai Tugas'),
            Button.text('⏸ Jeda Tugas'),
            Button.text('❌ Hapus Tugas'),
        ],
        [
            Button.text('▶️ Mulai Semua'),
            Button.text('⏸ Jeda Semua'),
            Button.text('❌ Hapus Semua')
        ],
        [
            Button.text('🔁 Ubah Download'),
            Button.text('❌ Kosongkan yang Telah Selesai'),
            Button.text('↩ Tutup Keyboard'),
        ],
    ]


def get_cancel():
    return [Button.inline('Batal', 'cancel')]


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
                Button.inline('Halaman Sebelumnya', data='up'),
                Button.inline(f'{page + 1}/{len(btns)}', data='jump'),
                Button.inline('Halaman Berikutnya', data='next')
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
            await bot.edit_message(msg, 'Pemilihan dibatalkan')
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
            page_btns = [Button.inline(f'Halaman {i + 1} {1 + i * line * size} - {(1 + i) * line * size}', data=str(i)) for i in range(len(btns))]
            page_btns = split_list(page_btns, 3)
            page_btns.append([Button.inline('Kembali', data='cancel')])
            await bot.edit_message(msg, 'Pilih halaman untuk melompat', buttons=page_btns)
            res_2 = await conv.wait_event(press_event(event))
            data_2 = res_2.data.decode()
            if data_2 == 'cancel':
                continue
            else:
                page = int(data_2)
                continue
        else:
            return res, data, msg
