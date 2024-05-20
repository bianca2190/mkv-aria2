#!/usr/bin/local/python
# -*- coding: utf-8 -*-
# Penulis: XuanPro, MKV mod

from aioaria2 import Aria2WebsocketClient
from aioaria2.exceptions import Aria2rpcException

from ariabot.util import getFileName


class Aria2Client:
    def __init__(self, rpc_url, rpc_token, bot, user):
        self.rpc_url = rpc_url
        self.rpc_token = rpc_token
        self.bot = bot
        self.user = user
        self.client = None

    async def init(self):
        try:
            self.client = await Aria2WebsocketClient.new(self.rpc_url, token=self.rpc_token)
            await self.client.getGlobalStat()
        except Aria2rpcException:
            await self.bot.send_message(self.user, 'Koneksi Aria2 gagal, harap periksa URL dan Token')
            return

        # Mendaftarkan event callback
        self.client.onDownloadStart(self.on_download_start)
        self.client.onDownloadPause(self.on_download_pause)
        self.client.onDownloadComplete(self.on_download_complete)
        self.client.onDownloadError(self.on_download_error)

    async def on_download_start(self, _trigger, data):
        gid = data['params'][0]['gid']
        # Memeriksa apakah file terikat dengan fitur khusus
        tellStatus = await self.client.tellStatus(gid)
        await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Tugas sudah mulai diunduh... \n Direktori unduhan: `{tellStatus["dir"]}`')

    async def on_download_pause(self, _trigger, data):
        gid = data['params'][0]['gid']
        tellStatus = await self.client.tellStatus(gid)
        await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Tugas berhasil dijeda')

    async def on_download_complete(self, _trigger, data):
        gid = data['params'][0]['gid']
        tellStatus = await self.client.tellStatus(gid)
        await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Tugas unduhan selesai')

    async def on_download_error(self, _trigger, data):
        gid = data['params'][0]['gid']
        tellStatus = await self.client.tellStatus(gid)
        errorCode = tellStatus['errorCode']
        errorMessage = tellStatus['errorMessage']
        if errorCode == '12':
            await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Tugas sedang diunduh, harap hapus dan coba lagi')
        else:
            await self.bot.send_message(self.user, errorMessage)
