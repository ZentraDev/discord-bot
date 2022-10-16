import asyncio
import logging
import os
from enum import Enum

import cooldowns
import disnake
from cooldowns import CallableOnCooldown
from disnake import TextChannel, Embed
from disnake.ext import commands
from disnake.ext.commands import InteractionBot, Param
from zentra import Message, Client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
channel: TextChannel | None = None


class Bucket(Enum):
    author = 1

    def process(self, *args, **kwargs):
        return kwargs["interaction"].author.id


async def main():
    bot = InteractionBot(test_guilds=[1030692828239642645])

    async def send_message(message: Message):
        global channel
        if not channel:
            channel = bot.get_channel(1031184781351845928)
            if not channel:
                channel = await bot.fetch_channel(1031184781351845928)

        await channel.send(
            embed=Embed(
                title=f"Name: {message.sender_name}", description=message.content
            ).set_footer(text=f"Conversation ID: {message.conversation_id}")
        )
        log.info(
            "> Message received from %s (%s)", message.sender_name, message.sender_id
        )

    client: Client = Client("Bot", call_on_message=send_message)
    await client.connect()

    @bot.slash_command()
    @cooldowns.cooldown(1, 1, Bucket.author)
    async def send_message(
        interaction: disnake.GuildCommandInteraction,
        content: str = Param(description="What you wish to say."),
        conversation_id: int
        | None = Param(
            default=1,
            description="The conversation you wish to send this message in.",
        ),
    ):
        """Send a message to a conversation."""
        await client.send_message(
            content=f"{interaction.author.display_name} said: {content}",
            conversation_id=conversation_id,
        )
        await interaction.send("I have sent that message for you.", ephemeral=True)
        log.info(
            "%s sent message '%s' to conversation %s",
            interaction.author.display_name,
            content,
            conversation_id,
        )

    @send_message.autocomplete("conversation_id")
    async def send_message_autocomplete(inter, user_input):
        user_input = str(user_input)
        possible_ids = await client.fetch_conversation_ids()
        possible_choices = [
            v for v in possible_ids if user_input.lower() in str(v).lower()
        ]
        if len(possible_choices) > 25:
            return []

        return possible_choices

    @bot.event
    async def on_slash_command_error(
        interaction: disnake.ApplicationCommandInteraction,
        exception: commands.CommandError,
    ) -> None:
        exception = getattr(exception, "original", exception)
        if isinstance(exception, CallableOnCooldown):
            return await interaction.send(
                embed=Embed(
                    title="Command on Cooldown",
                    description=f"Ahh man so fast! You must wait {exception.retry_after}"
                    f" seconds to run this command again",
                ),
                ephemeral=True,
            )

        raise exception

    await bot.start(token=os.environ["TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
