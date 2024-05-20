#!/usr/bin/local/python
# -*- coding: utf-8 -*-
# Author: XuanPro, MKV mod

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
            await self.bot.send_message(self.user, 'Aria2 connection error, please check the URL and Token')
            return

        # Register callback events
        self.client.onDownloadStart(self.on_download_start)
        self.client.onDownloadPause(self.on_download_pause)
        self.client.onDownloadComplete(self.on_download_complete)
        self.client.onDownloadError(self.on_download_error)

    async def on_download_start(self, _trigger, data):
        gid = data['params'][0]['gid']
        # Check if the file is bound with a specific characteristic
        tellStatus = await self.client.tellStatus(gid)
        await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Task has started downloading... \n Download directory: `{tellStatus["dir"]}`')

    async def on_download_pause(self, _trigger, data):
        gid = data['params'][0]['gid']
        tellStatus = await self.client.tellStatus(gid)
        await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Task has been successfully paused')

    async def on_download_complete(self, _trigger, data):
        gid = data['params'][0]['gid']
        tellStatus = await self.client.tellStatus(gid)
        await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Task download complete')

    async def on_download_error(self, _trigger, data):
        gid = data['params'][0]['gid']
        tellStatus = await self.client.tellStatus(gid)
        errorCode = tellStatus['errorCode']
        errorMessage = tellStatus['errorMessage']
        if errorCode == '12':
            await self.bot.send_message(self.user, f'{getFileName(tellStatus)}\n\n Task is already downloading, please delete and try again')
        else:
            await self.bot.send_message(self.user, errorMessage)
