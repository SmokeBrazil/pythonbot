import discord
import aiohttp
from discord.ext import commands
import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading

# ========================
# CONFIGURAÇÕES DO BOT
# ========================
TOKEN = "SEU_TOKEN_AQUI"  # ⚠️ Coloque seu token real do bot (NUNCA compartilhe publicamente!)
LOGIN = "Administrator"   # Nome de login (exemplo de uso interno)
SENHA = "sua_senha_aqui"  # Senha (⚠️ evite deixar hardcoded no código)
PORTA = 666               # Porta usada (para exibição no comando !dados)

# Lista de usuários autorizados a usar comandos restritos
ALLOWED_USERS = [381609335253499906, 305912287166988288]

# Informações do desenvolvedor/bot
DEV_NOME = "Smoke"
DEV_DISCORD = "@smokeoficial"
BOT_VERSAO = "1.0"

# ========================
# CONFIGURAÇÃO DO DISCORD
# ========================
intents = discord.Intents.default()
intents.message_content = True  # Necessário para ler mensagens de texto
bot = commands.Bot(command_prefix="!", intents=intents)

# ========================
# INTERFACE TKINTER (GUI)
# ========================
root = tk.Tk()
root.title("Logs de DM em tempo real")

# Caixa de texto para exibir logs
log_box = ScrolledText(root, width=80, height=20)
log_box.pack()

# Função para escrever no log (GUI + console)
def log_gui(texto):
    log_box.insert(tk.END, texto + "\n")
    log_box.see(tk.END)
    print(texto)

# ========================
# FUNÇÕES AUXILIARES
# ========================
async def get_external_ip():
    """Obtém o IP externo usando a API ipify"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.ipify.org?format=json") as resp:
                data = await resp.json()
                return data.get("ip", "Erro ao pegar IP")
    except Exception as e:
        return f"Erro: {e}"

def autorizado(ctx):
    """Verifica se o usuário está autorizado a usar comandos restritos"""
    return ctx.author.id in ALLOWED_USERS

# ========================
# COMANDOS DO BOT
# ========================
@bot.command(name="dados")
async def dados(ctx):
    """Envia IP, usuário e senha (restrito a usuários autorizados)"""
    if not autorizado(ctx):
        await ctx.reply("❌ Você não tem permissão para usar este comando.", mention_author=True)
        return

    ip = await get_external_ip()
    ip_porta = f"{ip}:{PORTA}"

    # Criação do embed com as informações
    embed = discord.Embed(title="🔎 Dados do Servidor", color=discord.Color.blue())
    embed.add_field(name="IP Externo", value=f"`{ip_porta}`", inline=False)
    embed.add_field(name="Usuário", value=f"`{LOGIN}`", inline=False)
    embed.add_field(name="Senha", value=f"`{SENHA}`", inline=False)

    # Tenta enviar por DM, se não conseguir manda no chat
    try:
        await ctx.author.send(embed=embed)
        log_gui(f"[ENVIADO] Para {ctx.author}: IP={ip_porta}, Usuário={LOGIN}, Senha={SENHA}")
        await ctx.reply("📩 Informações enviadas no seu DM.", mention_author=True)
    except discord.Forbidden:
        await ctx.send(embed=embed)
        log_gui(f"[FALHA] Não foi possível enviar DM para {ctx.author}")

@bot.command(name="info")
async def info(ctx):
    """Mostra informações do bot e do desenvolvedor"""
    embed = discord.Embed(title="ℹ️ Informações do Bot", color=discord.Color.green())
    embed.add_field(name="👨‍💻 Desenvolvido por", value=DEV_NOME, inline=False)
    embed.add_field(name="📌 Versão", value=BOT_VERSAO, inline=False)
    embed.add_field(name="💬 Contato", value=DEV_DISCORD, inline=False)
    embed.set_footer(text="Bot criado para gerenciamento de informações privadas.")
    await ctx.reply(embed=embed, mention_author=True)

@bot.command(name="falar")
async def falar(ctx, user: discord.User, *, mensagem: str):
    """Envia uma mensagem privada para o usuário especificado (restrito)"""
    if not autorizado(ctx):
        await ctx.reply("❌ Você não tem permissão para usar este comando.", mention_author=True)
        return

    try:
        await user.send(mensagem)
        log_gui(f"[ENVIADO] Para {user}: {mensagem}")
        await ctx.reply(f"✅ Mensagem enviada para {user.mention}", mention_author=True)
    except discord.Forbidden:
        await ctx.reply("⚠️ Não consegui enviar DM (usuário pode ter bloqueado).", mention_author=True)
        log_gui(f"[FALHA] Não foi possível enviar DM para {user}: {mensagem}")
    except Exception as e:
        await ctx.reply(f"❌ Erro ao enviar mensagem: {e}", mention_author=True)
        log_gui(f"[ERRO] Erro ao enviar DM para {user}: {mensagem} | Erro: {e}")

# Tratamento de erros do comando !falar
@falar.error
async def falar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("❌ Uso incorreto! Exemplo:\n`!falar @usuario mensagem`", mention_author=True)
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("❌ Usuário inválido! Use a menção: `@usuario`", mention_author=True)
    else:
        await ctx.reply(f"❌ Ocorreu um erro: {error}", mention_author=True)

@bot.command(name="ping")
async def ping(ctx):
    """Verifica a latência do bot"""
    await ctx.reply(f"Pong! Latência {round(bot.latency*1000)}ms", mention_author=True)

# ========================
# EVENTOS DO BOT
# ========================
@bot.event
async def on_message(message):
    """Loga mensagens recebidas em DM"""
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        log_gui(f"[RECEBIDO] De {message.author}: {message.content}")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    """Trata erros de comandos inexistentes ou outros problemas"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply(f"❌ Comando não encontrado: `{ctx.message.content}`", mention_author=True)
    else:
        print(f"Erro no comando {ctx.message.content}: {error}")

# ========================
# EXECUÇÃO (THREAD + GUI)
# ========================
def run_bot():
    """Inicia o bot do Discord em uma thread separada"""
    bot.run(TOKEN)

# Rodando o bot em thread para não travar a interface Tkinter
threading.Thread(target=run_bot).start()

# Inicia o loop da interface Tkinter
root.mainloop()
