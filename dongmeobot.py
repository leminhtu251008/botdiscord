import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
import sys
import traceback

ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe') if hasattr(sys, '_MEIPASS') else 'ffmpeg'

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    TEMP_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)
    TEMP_DIR = BASE_DIR

OPUS_PATH = os.path.join(BASE_DIR, "libopus.dll")

if not os.path.exists(OPUS_PATH):
    print("❌ Không tìm thấy libopus.dll!")
    sys.exit(1)

discord.opus.load_opus(OPUS_PATH)

temp_token_file_path = os.path.join(TEMP_DIR, 'bot_token.txt')
if os.path.exists(temp_token_file_path):
    with open(temp_token_file_path, 'r') as file:
        BOT_TOKEN = file.read().strip()
else:
    BOT_TOKEN = input("Nhập token của bot: ")
    with open(temp_token_file_path, 'w') as file:
        file.write(BOT_TOKEN)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable=ffmpeg_path, **ffmpeg_options), data=data)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
music_queue = []

@bot.event
async def on_ready():
    print(f': {bot.user.name}')

def play_next(ctx):
    if music_queue:
        next_song = music_queue.pop(0)
        coro = play(ctx, next_song, autoplay=True)
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        fut.result()

@bot.command(name='choi', help='Chơi nhạc từ link youtube')
async def play(ctx, url, autoplay=False):
    if not ctx.message.author.voice:
        await ctx.send(f"{ctx.message.author.name} chưa tham gia voice channel nào cả!")
        return

    channel = ctx.message.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if not voice_client or not voice_client.is_connected():
        try:
            voice_client = await channel.connect()
        except Exception as e:
            await ctx.send(f"⚠️ Không thể kết nối đến kênh thoại: {str(e)}")
            return

    if voice_client.is_playing() and not autoplay:
        music_queue.append(url)
        await ctx.send(f'🎵 Đã thêm vào hàng đợi: {url}')
        return

    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            def after_playback(error):
                if error:
                    print(f"🔴 FFmpeg Playback Lỗi: {error}")
                else:
                    print("✅ Chơi Nhạc Thành Công!")
                play_next(ctx)
            voice_client.play(player, after=after_playback)
            await ctx.send(f'🎶 Đang chơi: {player.title}')
        except Exception as e:
            traceback.print_exc()
            await ctx.send(f"⚠️ Đã có lỗi xảy ra: {str(e)}")

@bot.command(name='hangdoi', help='Hiển thị danh sách phát')
async def queue(ctx):
    if music_queue:
        queue_list = '\n'.join(music_queue)
        await ctx.send(f'📜 Hàng đợi: {queue_list}')
    else:
        await ctx.send("🎶 Hàng đợi trống!")

@bot.command(name='boqua', help='Bỏ qua bài hát hiện tại')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Đã bỏ qua bài hát!")
    else:
        await ctx.send("⚠️ Không có bài hát nào đang phát!")

@bot.command(name='dung', help='Dừng phát nhạc và rời kênh')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        music_queue.clear()
        await ctx.send("⏹️ Đã dừng nhạc và rời kênh!")

bot.run(BOT_TOKEN)