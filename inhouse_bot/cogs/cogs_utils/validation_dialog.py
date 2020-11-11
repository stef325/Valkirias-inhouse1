import asyncio
from typing import Tuple, Optional, List, Set

import discord
from discord.ext.commands import Bot

from inhouse_bot.bot_orm import Player


async def checkmark_validation(
    bot: Bot,
    message: discord.Message,
    validating_players: List[Player],
    validation_threshold: int = 10,
    timeout=120.0,
) -> Tuple[bool, Optional[Set[int]]]:
    """
    Implements a checkmark validation on the chosen message.

    3 possible outcomes:
        True and None
            It was validated by the necessary number of players
        False with a list of players who did not validate
            It timed out and the players who didn't validate should be dropped
        False with the the player who cancelled (in a list)
            It was cancelled and the player should be dropped
    """

    validating_players_ids = [p.id for p in validating_players]

    await message.add_reaction("✅")
    await message.add_reaction("❎")

    def check(received_reaction: discord.Reaction, sending_user: discord.User):
        # This check is simply used to see if a player in the game responded to the message.
        return (
            received_reaction.message.id == message.id
            and sending_user.id in validating_players_ids
            and str(received_reaction.emoji) in ["✅", "❎"]
        )

    ids_of_players_who_validated = set()
    try:
        while len(ids_of_players_who_validated) < validation_threshold:
            reaction, user = await bot.wait_for("reaction_add", timeout=timeout, check=check)

            # A player accepted, we keep him in memory
            if str(reaction.emoji) == "✅":
                ids_of_players_who_validated.add(user.id)

            # A player cancels, we return it and will drop him
            elif str(reaction.emoji) == "❎":
                return False, set(user.id)

    # We get there if no player accepted in the last x minutes
    except asyncio.TimeoutError:
        return False, set(i for i in validating_players_ids if i not in ids_of_players_who_validated)

    # Finally, we arrive here only if the while loop brok
    return True, None
