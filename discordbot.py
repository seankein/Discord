import discord
import config
import random
import datetime
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 試合参加登録用のグローバルリスト
match_list = []

@bot.event
async def on_ready():
    schedule_daily_match()  # スケジュールジョブの登録を実行
    scheduler.start()
    print("Ready!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        answer_list = ["さすがですね！", "知らなかったです！", "すごいですね！", "センスが違いますね！", "そうなんですか？"]
        answer = random.choice(answer_list)
        await message.channel.send(answer)
    if message.content == '/neko':
        await message.channel.send('にゃーん')
    
    await bot.process_commands(message)

@bot.command(name="register_team")
async def register_team(ctx, *, team_name: str):
    guild = ctx.guild
    team_role = discord.utils.get(guild.roles, name=team_name)
    
    if team_role:
        # ロールは存在するので、ユーザーが既に持っているかチェック
        if team_role in ctx.author.roles:
            await ctx.send("あなたは既にこのチームに登録されています。")
        else:
            try:
                await ctx.author.add_roles(team_role)
                await ctx.send(f"既存のチームロール **{team_name}** をあなたに付与しました。")
            except Exception as e:
                await ctx.send(f"ロールの付与中にエラーが発生しました: {e}")
    else:
        try:
            # ランダムな色を生成（0x000000～0xFFFFFF）
            random_color = discord.Colour(random.randint(0, 0xFFFFFF))
            team_role = await guild.create_role(name=team_name, colour=random_color)
            await ctx.author.add_roles(team_role)
            await ctx.send(f"ようこそ **{team_name}** 。チームロールを作成し、あなたに付与しました。")
        except Exception as e:
            await ctx.send(f"ロールの作成中にエラーが発生しました: {e}")

@bot.command(name="delete_team")
async def delete_team(ctx, *, team_name: str):
    guild = ctx.guild
    team_role = discord.utils.get(guild.roles, name=team_name)
    leader_role_name = f"{team_name}リーダー"
    leader_role = discord.utils.get(guild.roles, name=leader_role_name)
    
    # チームロールが存在しない場合
    if not team_role:
        await ctx.send("指定されたチームロールは存在しません。")
        return

    # チーム削除はリーダーのみが実行できる
    if not leader_role or (leader_role not in ctx.author.roles):
        await ctx.send("チームの削除はそのチームのリーダーのみが実行できます。")
        return

    # 削除処理: チームロールとリーダーロールの両方を削除
    try:
        await team_role.delete()
        if leader_role:
            await leader_role.delete()
        await ctx.send(f"チームロール **{team_name}** とリーダーロール **{leader_role_name}** を削除しました。")
    except Exception as e:
        await ctx.send(f"チームの削除中にエラーが発生しました: {e}")

@bot.command(name="set_leader")
async def set_leader(ctx, *, team_name: str):
    guild = ctx.guild
    team_role = discord.utils.get(guild.roles, name=team_name)
    if not team_role:
        await ctx.send("指定されたチームが存在しません。先にチーム登録してください。")
        return
    if team_role not in ctx.author.roles:
        await ctx.send("あなたはこのチームに参加していないため、リーダーロールを付与できません。")
        return

    leader_role_name = f"{team_name}リーダー"
    leader_role = discord.utils.get(guild.roles, name=leader_role_name)
    
    # すでにリーダーロールが存在する場合は、誰かに付与されているかをチェック
    if leader_role:
        # 既にリーダーロールを持っているユーザーがいる場合（かつ自分以外）
        if leader_role.members and (ctx.author not in leader_role.members):
            await ctx.send("このチームのリーダーは既に存在しています。")
            return
        else:
            # 自分が既に持っている場合、色を更新
            try:
                await leader_role.edit(colour=team_role.colour)
                await ctx.send(f"あなたは既にこのチームのリーダーです。リーダーロールの色を更新しました。")
            except Exception as e:
                await ctx.send(f"リーダーロールの色更新中にエラーが発生しました: {e}")
            return
    else:
        try:
            # チームロールと同じ色でリーダーロールを作成し、自分に付与
            leader_role = await guild.create_role(name=leader_role_name, colour=team_role.colour)
            await ctx.author.add_roles(leader_role)
            await ctx.send(f"リーダーロール **{leader_role_name}** を作成し、あなたに付与しました。")
        except Exception as e:
            await ctx.send(f"リーダーロールの作成中にエラーが発生しました: {e}")

@bot.command(name="remove_leader")
async def remove_leader(ctx, *, team_name: str):
    guild = ctx.guild
    leader_role_name = f"{team_name}リーダー"
    leader_role = discord.utils.get(guild.roles, name=leader_role_name)
    if not leader_role:
        await ctx.send("指定されたリーダーロールは存在しません。")
        return
    if leader_role not in ctx.author.roles:
        await ctx.send("あなたはこのリーダーロールを持っていません。")
        return
    try:
        await ctx.author.remove_roles(leader_role)
        await ctx.send(f"リーダーロール **{leader_role_name}** を削除しました。")
    except Exception as e:
        await ctx.send(f"リーダーロールの削除中にエラーが発生しました: {e}")

@bot.command(name="my_teams")
async def my_teams(ctx):
    leader_teams = []
    for role in ctx.author.roles:
        if role.name.endswith("リーダー"):
            team_name = role.name[:-4]
            leader_teams.append(team_name)
    if leader_teams:
        await ctx.send(f"あなたがリーダーであるチーム: {', '.join(leader_teams)}")
    else:
        await ctx.send("あなたはどのチームのリーダーにもなっていません。")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("そのコマンドは認識されません。利用可能なコマンドは !commands で確認できます。")
    else:
        raise error
    
# ----- 試合参加登録関連コマンド -----

@bot.command(name="join")
async def join_match(ctx, *, team_name: str):
    guild = ctx.guild
    leader_role = discord.utils.get(guild.roles, name=f"{team_name}リーダー")
    if not leader_role or (leader_role not in ctx.author.roles):
        await ctx.send("あなたはこのチームのリーダーではありません。")
        return
    if team_name in match_list:
        await ctx.send("このチームは既に試合参加に登録されています。")
    else:
        match_list.append(team_name)
        await ctx.send(f"【{team_name}】が試合参加に登録されました。")

@bot.command(name="cancel")
async def cancel_match(ctx, *, team_name: str):
    guild = ctx.guild
    leader_role = discord.utils.get(guild.roles, name=f"{team_name}リーダー")
    if not leader_role or (leader_role not in ctx.author.roles):
        await ctx.send("あなたはこのチームのリーダーではありません。")
        return
    if team_name in match_list:
        match_list.remove(team_name)
        await ctx.send(f"【{team_name}】の試合参加登録が取り消されました。")
    else:
        await ctx.send("このチームは試合参加に登録されていません。")

# マッチング処理を実行する関数
async def run_match():
    # ここでは config.MATCH_CHANNEL_ID で指定されたチャンネルに結果を発表する
    channel = bot.get_channel(config.MATCH_CHANNEL_ID)
    if not channel:
        print("マッチング発表用チャンネルが見つかりません。")
        return

    if len(match_list) < 2:
        await channel.send("試合に参加するチームが不足しています。")
    else:
        teams = match_list.copy()
        random.shuffle(teams)
        matches = []
        while len(teams) >= 2:
            team1 = teams.pop()
            team2 = teams.pop()
            matches.append((team1, team2))
        unmatched = teams[0] if teams else None

        for idx, (t1, t2) in enumerate(matches, start=1):
            role1 = discord.utils.get(channel.guild.roles, name=t1)
            role2 = discord.utils.get(channel.guild.roles, name=t2)
            mention1 = role1.mention if role1 else t1
            mention2 = role2.mention if role2 else t2
            await channel.send(f"matching{idx} : {mention1} vs {mention2}")
        if unmatched:
            await channel.send(f"【{unmatched}】は対戦相手が見つかりませんでした。")
    match_list.clear()
    await channel.send("マッチングが完了しました。参加リストを初期化します。")

# APSchedulerの設定
scheduler = AsyncIOScheduler()

def schedule_daily_match():
    # 毎日18:00にrun_matchを実行するジョブをスケジュール
    scheduler.add_job(
        lambda: bot.loop.create_task(run_match()),
        trigger='cron',
        hour=17,
        minute=35,
        id='daily_match'
    )
    print("毎日18:00のマッチングジョブをスケジュールしました。")

@bot.command(name="commands")
async def custom_help(ctx):
    help_text = (
        "**コマンド一覧**\n\n"
        "**チーム管理**\n"
        "• `!register_team <チーム名>`: チームに登録（存在しない場合は作成し、付与）\n"
        "• `!delete_team <チーム名>`: チームの削除（リーダーのみ実行可能。チームロールとリーダーロールを削除）\n"
        "• `!set_leader <チーム名>`: チームのリーダーロールを付与（既にリーダーがいる場合は新規付与不可、色はチームロールと同一）\n"
        "• `!remove_leader <チーム名>`: リーダーロールを削除\n"
        "• `!my_teams`: あなたがリーダーであるチーム一覧を表示\n\n"
        "**試合参加登録・マッチング**\n"
        "• `!join <チーム名>`: リーダーのみ、試合参加に登録（チーム名をリストに追加）\n"
        "• `!cancel <チーム名>`: リーダーのみ、試合参加登録を取消（リストから除外）\n"
        "• `!match`: リーダーが手動でマッチング処理を実行\n"
        "　　※毎日設定時刻（例：18:00）には自動でマッチング処理が実行され、結果は専用チャンネルに投稿されます\n\n"
        "**その他**\n"
        "• `/neko`: にゃーんと返答\n"
    )
    await ctx.send(help_text)

bot.run(config.DISCORD_TOKEN)


