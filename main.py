import discord
from discord.ext import commands
from Websocket.websocket import WebSocket

class DisplayTrivia(commands.Cog, WebSocket):
    
    def __init__(self, client):
        super().__init__(client)
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = f"with Display Trivia!", url = "https://app.displaysocial.com")
        await self.client.change_presence(activity=game)
        
    @commands.command(aliases = ["open"])
    async def start(self, ctx):
        if self.ws:
            if self.ws.open:
                return await self.send_hook("**Websocket Already Opened!**")
        await self.send_hook("**Websocket Opened!**")
        await self.connect_ws()
        
            
    @commands.command()
    async def close(self, ctx):
        await self.close_ws()
            
client = commands.Bot(command_prefix = ">")
client.add_cog(DisplayTrivia(client))
            
client.run("bot_token")
