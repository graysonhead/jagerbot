from . import nlu_engine
import json
from . import client
from discord import ChannelType
from enum import Enum


class Action(object):

    def render_description(self):
        return "Null action"


class SendMessage(Action):

    def __init__(self, message, channel):
        self.message = message
        self.channel = channel

    async def execute(self):
        await self.channel.send(self.message)

    def render_description(self):
        return f"Send message to channel {self.channel}: {self.message}"


async def respond(message):
    if "?actions" in message.content:
        content = message.content.replace("?actions", "")
        render_actions = True
    else:
        render_actions = False
        content = message.content
    if "?intent" in content:
        content = content.replace("?intent", "")
        parsing = nlu_engine.parse(content)
        await message.channel.send(json.dumps(parsing, indent=2))
    else:
        parsing = nlu_engine.parse(content)
    actions = []

    for action in actions:
        if render_actions:
            await message.channel.send(f"Executing action: {action.render_description()}")
        try:
            await action.execute()
        except Exception as e:
            await message.channel.send(f"Action execution failed: {e}")
            raise
