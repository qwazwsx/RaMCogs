import discord
from discord.ext import commands
from discord import client
from redbot.core import Config, bank
import asyncio

from collections import OrderedDict

class Leaderboard:

    def __init__(self, bot):
        print('Loaded Leaderboard')
        self.boss_last_leaderboard = None
        self.last_leaderboard = None
        self.last_richest_user = None
        self.last_most_kills_user = None
        self.last_most_kills_users = []
        self.bot = bot
        self.config = Config.get_conf(self, 8358350000, force_registration=True)

        self.guild = 278639962558300160
        self.boss_channel = 474801276408954891
        self.boss_message = 482438653776494605

        self.bal_channel = 474801276408954891
        self.bal_message = 482438585736495104

        print('[Leaderboard] task create')
        self.bot.loop.create_task(self.update_leaderboard())
        self.bot.loop.create_task(self.update_boss_leaderboard())
        self.bot.loop.create_task(self.update_leader_roles())


    """
    sends and handles updates for boss leaderboard
    """
    async def update_boss_leaderboard(self):
        while self == self.bot.get_cog('Leaderboard'):
            #print('[Leaderboard] boss loop')
            channel = self.bot.get_channel(self.boss_channel)
            message = await channel.get_message(self.boss_message)

            leaderboard = await self._boss_leaderboard()

            if self.boss_last_leaderboard != leaderboard:
                await message.edit(content=str(leaderboard))
                self.boss_last_leaderboard = Leaderboard

            await asyncio.sleep(5)


    """
    generates message for boss leaderboard
    """
    async def _boss_leaderboard(self):
        boss = self.bot.get_cog('Events')
        stats = await boss.get_boss_kills(self.guild)
        unsorted_board = {}

        # re format board so we can sort it
        for user, value in stats.items():
            unsorted_board[user] = int(value['kills'])

        sorted_board = sorted(OrderedDict(unsorted_board).items(), key=lambda x:-x[1])

        # create leaderboard
        leaderboard_message = "```md\n" + f"{f'#':4}{f'Name':36}{f'Boss Kills':2}\n"
        for i, d in enumerate(sorted_board):
            try:
                user = self.bot.get_user(int(d[0])).name
            except AttributeError:
                i = i - 1
                continue
            leaderboard_message = leaderboard_message + f"{f''+str(i+1)+'.':4}{f''+user:36}{f''+str(d[1]):2}\n"
        leaderboard_message = leaderboard_message + '```'

        return leaderboard_message

    """Returns a list of shit"""
    async def _sorted_boss_kills(self):
        boss = self.bot.get_cog('Events')
        stats = await boss.get_boss_kills(self.guild)
        unsorted_board = {}

        # re format board so we can sort it
        for user, value in stats.items():
            unsorted_board[user] = int(value['kills'])

        return sorted(OrderedDict(unsorted_board).items(), key=lambda x:-x[1])


    """
    updates the leaderboard by either making a new message if none exists or editing an existing message
    """
    async def update_leaderboard(self):
        while self == self.bot.get_cog('Leaderboard'):
            print('[Leaderboard][loop] top')

            channel = self.bot.get_channel(self.bal_channel)
            message = await channel.get_message(self.bal_message)
    
            print('[Leaderboard][loop] got channel and message')
            
            leaderboard = await self._leaderboard(message)

            print('[Leaderboard][loop] got leaderboard data')

            
            if self.last_leaderboard != leaderboard:
                print('[Leaderboard][loop] inside if, going to edit')
                await message.edit(content=str(leaderboard))
                self.last_leaderboard = Leaderboard

            print('[Leaderboard][loop] end')
            await asyncio.sleep(5)



    """
    taken from the economy cog (https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/cogs/economy/economy.py#L309) 

    Arguments:
        ctx: d.py message object that we can derive the guild from

    Returns:
        leaderboard in text form
    """
    async def _leaderboard(self, ctx):
        print('[Leaderboard][fetch] top')
        top = 10
        show_global = False


        guild = ctx.guild
        if (
            await bank.is_global() and show_global
        ):  # show_global is only applicable if bank is global
            guild = None
        bank_sorted = await bank.get_leaderboard(positions=top, guild=guild)
        if len(bank_sorted) < top:
            top = len(bank_sorted)
        header = f"{f'#':4}{f'Name':36}{f'Score':2}\n"
        highscores = [
            (
                f"{f'{pos}.': <{3 if pos < 10 else 2}} {acc[1]['name']: <{35}s} "
                f"{acc[1]['balance']: >{2 if pos < 10 else 1}}\n"
            )
            for pos, acc in enumerate(bank_sorted, 1)
        ]
        if highscores:
            pages = [
                f"```md\n{header}{''.join(''.join(highscores[x:x + 10]))}```"
                for x in range(0, len(highscores), 10)
            ]

            print('[Leaderboard][fetch] end')

            return pages[0]



    """
    Updates the "leader" roles on a timed loop.
    """
    async def update_leader_roles(self):
        while self == self.bot.get_cog('Leaderboard'):
            #print('[Leaderboard] role loop')
            
            guild = self.bot.get_guild(278639962558300160)
            self.gconf = self.config.guild(guild)

            await self._most_money_role(guild)
            await self._most_kills_roles(guild)

            await asyncio.sleep(10)


    """
    gives the user with the highest balance a special role
    We're using the config so we don't get duplicate people with roles.
    """
    async def _most_money_role(self, guild):
            # Constants
            function = "richest_user"
            role_id = 484130508582682635
            role = discord.utils.get(guild.roles, id=role_id)
            
            top_user_list = await bank.get_leaderboard(positions=1, guild=guild) 
            top_user_tuple =top_user_list[0]
            top_user_id = top_user_tuple[0]
            top_user = guild.get_member(top_user_id) # Member object

            # Runs if there's a new top_user (or if the cog reloaded).
            if self.last_richest_user != top_user.id:
                await self._update_most_x_role(role, guild, top_user, function)

            self.last_richest_user = top_user.id
    
    """
    gives the user with the most kills.
    We're using the config so we don't get duplicate people with roles.
    """
    async def _most_kills_roles(self, guild):
            # Constants
            function = "most_kills_users"
            role_id = 484104431835545600
            role_users_nr = 3

            role = discord.utils.get(guild.roles, id=role_id)
            
            #sorted_board = self._sorted_boss_kills
            boss = self.bot.get_cog('Events')
            stats = await boss.get_boss_kills(self.guild)
            unsorted_board = {}

            # re format board so we can sort it
            for user, value in stats.items():
                unsorted_board[user] = int(value['kills'])
            
            
            sorted_board = sorted(OrderedDict(unsorted_board).items(), key=lambda x:-x[1])
            
            """for i, d in enumerate(sorted_board):
                top_user_id = self.bot.get_user(int(d[0])).id
                if i-1 == role_users_nr:
                    break"""

            top_users_ids = []
            top_users = []
        
            for i, d in enumerate(sorted_board):
                top_users_ids.append(self.bot.get_user(int(d[0])).id)
                if i+1 == role_users_nr:
                    break

            #top_user = guild.get_member(top_user_id) # Member object

            for id in top_users_ids:
                top_users.append(guild.get_member(id))

            # Only runs if there are new top 3s.
            if  self.last_most_kills_users != top_users_ids:
                try:
                    curr_top_users = await self.gconf.get_raw(function)
                except KeyError:
                    curr_top_users = []

                # Removes a user's role if he is not one of the current top 3.
                for user_id in curr_top_users:
                    tempuser = guild.get_member(user_id)
                    await tempuser.remove_roles(role)

                # Gives all top users the role IF they are not in the last top users(removes dupe role giving.).
                for user_id in top_users_ids:
                    tempuser = guild.get_member(user_id)
                    await tempuser.add_roles(role)

                self.last_most_kills_users = top_users_ids
                await self.gconf.set_raw(function, value=top_users_ids)
        
    

    # Updates/removes a user's role based on which "function" it receives.
    async def _update_most_x_role(self, role, guild, top_user, function):
        try:
            curr_top_user_id = await self.gconf.get_raw(function)
            curr_top_user = guild.get_member(curr_top_user_id)
        except KeyError:
            print("The errors")
            curr_top_user = None

        if curr_top_user is not None:
            await curr_top_user.remove_roles(role)
            
        await self.gconf.set_raw(function, value=top_user.id)
        await top_user.add_roles(role)
        



        
