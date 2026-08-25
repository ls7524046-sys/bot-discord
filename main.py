import discord
import random
import asyncio
import os
import json
import time
import aiohttp
import datetime

from zoneinfo import ZoneInfo
from discord.ext import commands, tasks


# =========================================================
# CONFIGURAÇÕES
# =========================================================

TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIXO = "."

# Canal de BOT ONLINE
ONLINE_CHANNEL_ID = os.environ.get("ONLINE_CHANNEL_ID")

# Canal onde serão anunciados os destaques
DESTAQUE_CHANNEL_ID = os.environ.get("DESTAQUE_CHANNEL_ID")

# Cargo dado ao TOP 1
TOP1_ROLE_ID = os.environ.get("TOP1_ROLE_ID")


intents = discord.Intents.default()

intents.message_content = True
intents.members = True


bot = commands.Bot(
    command_prefix=PREFIXO,
    intents=intents,
    help_command=None
)


# =========================================================
# ARQUIVOS
# =========================================================

RANK_FILE = "rank.json"
AFK_FILE = "afk.json"


# =========================================================
# DADOS
# =========================================================

rank_mensagens = {}
afk_usuarios = {}

# Controle do CL
cl_ativo = {}
cl_cooldown = {}

CL_COOLDOWN = 600

# Controle do ranking semanal
top_anterior = {}
top1_anterior = {}

# Controle do último reset
ultimo_reset = None

# Fuso horário de São Paulo
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


# =========================================================
# FUNÇÕES DE ARQUIVO
# =========================================================

def carregar_json(arquivo):

    if not os.path.exists(arquivo):
        return {}

    try:

        with open(
            arquivo,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as erro:

        print(
            f"⚠️ Erro ao carregar {arquivo}: {erro}"
        )

        return {}


def salvar_json(arquivo, dados):

    try:

        with open(
            arquivo,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                dados,
                f,
                indent=4,
                ensure_ascii=False
            )

    except Exception as erro:

        print(
            f"⚠️ Erro ao salvar {arquivo}: {erro}"
        )


# =========================================================
# CARREGA OS DADOS
# =========================================================

rank_mensagens = carregar_json(
    RANK_FILE
)

afk_usuarios = carregar_json(
    AFK_FILE
)


# =========================================================
# FUNÇÕES DO RANKING
# =========================================================

def obter_ranking(guild):

    guild_id = str(
        guild.id
    )

    dados = rank_mensagens.get(
        guild_id,
        {}
    )

    return sorted(
        dados.items(),
        key=lambda x: x[1],
        reverse=True
    )


async def enviar_destaque(
    guild,
    membro
):

    if not DESTAQUE_CHANNEL_ID:
        return

    try:

        canal = bot.get_channel(
            int(DESTAQUE_CHANNEL_ID)
        )

        if not canal:
            print(
                "⚠️ Canal de destaque não encontrado."
            )
            return

        await canal.send(
            f"🌟 **{membro.display_name} agora é destaque "
            f"da semana do nosso servidor!** 🏆"
        )

    except Exception as erro:

        print(
            f"⚠️ Erro ao enviar destaque: {erro}"
        )


async def atualizar_cargo_top1(
    guild,
    novo_top1_id
):

    if not TOP1_ROLE_ID:
        return

    try:

        cargo = guild.get_role(
            int(TOP1_ROLE_ID)
        )

        if not cargo:

            print(
                f"⚠️ Cargo TOP 1 não encontrado "
                f"no servidor {guild.name}."
            )

            return

        guild_id = str(
            guild.id
        )

        antigo_top1_id = top1_anterior.get(
            guild_id
        )

        # -------------------------------------------------
        # REMOVE O CARGO DO ANTIGO TOP 1
        # -------------------------------------------------

        if (
            antigo_top1_id
            and antigo_top1_id != novo_top1_id
        ):

            antigo_membro = guild.get_member(
                int(antigo_top1_id)
            )

            if (
                antigo_membro
                and cargo in antigo_membro.roles
            ):

                try:

                    await antigo_membro.remove_roles(
                        cargo,
                        reason="Novo TOP 1 semanal"
                    )

                    print(
                        f"🔄 Cargo TOP 1 removido de "
                        f"{antigo_membro}."
                    )

                except discord.Forbidden:

                    print(
                        f"⚠️ Não consegui remover o cargo "
                        f"de {antigo_membro}."
                    )

        # -------------------------------------------------
        # ADICIONA O CARGO AO NOVO TOP 1
        # -------------------------------------------------

        novo_membro = guild.get_member(
            int(novo_top1_id)
        )

        if not novo_membro:
            return

        if cargo not in novo_membro.roles:

            try:

                await novo_membro.add_roles(
                    cargo,
                    reason="Novo TOP 1 semanal"
                )

                print(
                    f"👑 {novo_membro} agora é TOP 1!"
                )

            except discord.Forbidden:

                print(
                    "⚠️ Não consegui dar o cargo "
                    "ao novo TOP 1."
                )

        top1_anterior[
            guild_id
        ] = str(novo_top1_id)

    except Exception as erro:

        print(
            f"⚠️ Erro ao atualizar cargo TOP 1: {erro}"
        )


async def verificar_ranking(guild):

    guild_id = str(
        guild.id
    )

    ranking = obter_ranking(
        guild
    )

    if not ranking:
        return

    # -----------------------------------------------------
    # TOP 10 ATUAL
    # -----------------------------------------------------

    top_atual = {
        str(user_id)
        for user_id, quantidade in ranking[:10]
    }

    top_antigo = top_anterior.get(
        guild_id,
        set()
    )

    # -----------------------------------------------------
    # DESCOBRE QUEM ENTROU NO TOP 10
    # -----------------------------------------------------

    novos_destaques = (
        top_atual - top_antigo
    )

    for user_id in novos_destaques:

        membro = guild.get_member(
            int(user_id)
        )

        if membro:

            await enviar_destaque(
                guild,
                membro
            )

    # -----------------------------------------------------
    # ATUALIZA TOP 10
    # -----------------------------------------------------

    top_anterior[
        guild_id
    ] = top_atual

    # -----------------------------------------------------
    # VERIFICA TOP 1
    # -----------------------------------------------------

    novo_top1_id = str(
        ranking[0][0]
    )

    antigo_top1_id = top1_anterior.get(
        guild_id
    )

    if novo_top1_id != antigo_top1_id:

        await atualizar_cargo_top1(
            guild,
            novo_top1_id
        )


def preparar_ranking_inicial():

    """
    Carrega o TOP 10 existente quando o bot inicia.
    Isso evita que todos os usuários existentes
    sejam anunciados novamente como destaque.
    """

    for guild in bot.guilds:

        guild_id = str(
            guild.id
        )

        ranking = obter_ranking(
            guild
        )

        if not ranking:
            continue

        top_anterior[
            guild_id
        ] = {
            str(user_id)
            for user_id, quantidade in ranking[:10]
        }

        top1_anterior[
            guild_id
        ] = str(
            ranking[0][0]
        )


# =========================================================
# RESET SEMANAL
# =========================================================

async def executar_reset_semanal():

    global ultimo_reset

    agora = datetime.datetime.now(
        FUSO_HORARIO
    )

    chave_reset = agora.strftime(
        "%Y-%m-%d"
    )

    # Evita executar duas vezes no mesmo dia
    if ultimo_reset == chave_reset:
        return

    # Segunda-feira
    if agora.weekday() != 0:
        return

    # Só executa nos primeiros minutos da segunda
    if agora.hour != 0:
        return

    ultimo_reset = chave_reset

    print(
        "🔄 Iniciando reset semanal do ranking..."
    )

    for guild in bot.guilds:

        guild_id = str(
            guild.id
        )

        # -------------------------------------------------
        # REMOVE CARGO DO ANTIGO TOP 1
        # -------------------------------------------------

        if TOP1_ROLE_ID:

            try:

                cargo = guild.get_role(
                    int(TOP1_ROLE_ID)
                )

                antigo_top1_id = top1_anterior.get(
                    guild_id
                )

                if cargo and antigo_top1_id:

                    membro = guild.get_member(
                        int(antigo_top1_id)
                    )

                    if (
                        membro
                        and cargo in membro.roles
                    ):

                        await membro.remove_roles(
                            cargo,
                            reason="Reset semanal do ranking"
                        )

                        print(
                            f"🗑️ Cargo removido de "
                            f"{membro}."
                        )

            except discord.Forbidden:

                print(
                    f"⚠️ Não consegui remover o cargo "
                    f"do antigo TOP 1 em {guild.name}."
                )

            except Exception as erro:

                print(
                    f"⚠️ Erro ao remover cargo no reset: {erro}"
                )

        # -------------------------------------------------
        # ZERA O RANKING
        # -------------------------------------------------

        rank_mensagens[
            guild_id
        ] = {}

        # -------------------------------------------------
        # LIMPA CONTROLES
        # -------------------------------------------------

        top_anterior.pop(
            guild_id,
            None
        )

        top1_anterior.pop(
            guild_id,
            None

        )

    # -----------------------------------------------------
    # SALVA O RANKING ZERADO
    # -----------------------------------------------------

    salvar_json(
        RANK_FILE,
        rank_mensagens
    )

    print(
        "✅ Ranking semanal resetado com sucesso!"
    )


@tasks.loop(minutes=1)
async def verificar_reset_semanal():

    try:

        await executar_reset_semanal()

    except Exception as erro:

        print(
            f"⚠️ Erro no reset semanal: {erro}"
        )


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    print("=" * 50)
    print(
        f"✅ Bot online: {bot.user}"
    )
    print(
        f"🆔 ID: {bot.user.id}"
    )
    print(
        f"📌 Prefixo: {PREFIXO}"
    )
    print("=" * 50)

    # -----------------------------------------------------
    # PREPARA RANKING EXISTENTE
    # -----------------------------------------------------

    preparar_ranking_inicial()

    # -----------------------------------------------------
    # INICIA SISTEMA DE RESET
    # -----------------------------------------------------

    if not verificar_reset_semanal.is_running():

        verificar_reset_semanal.start()

    # -----------------------------------------------------
    # MENSAGEM ONLINE
    # -----------------------------------------------------

    if ONLINE_CHANNEL_ID:

        try:

            canal = bot.get_channel(
                int(ONLINE_CHANNEL_ID)
            )

            if canal:

                embed = discord.Embed(
                    title="🟢 BOT ONLINE",
                    description=(
                        f"**{bot.user.name}** está online "
                        "e funcionando normalmente!"
                    ),
                    color=discord.Color.green()
                )

                embed.set_footer(
                    text="Sistema automático"
                )

                await canal.send(
                    embed=embed
                )

        except Exception as erro:

            print(
                f"⚠️ Erro ao enviar mensagem ONLINE: {erro}"
            )


# =========================================================
# CONTADOR DE MENSAGENS / AFK
# =========================================================

@bot.event
async def on_message(message):

    # Ignora bots
    if message.author.bot:
        return

    # -----------------------------------------------------
    # RANK
    # -----------------------------------------------------

    guild_id = (
        str(message.guild.id)
        if message.guild
        else None
    )

    user_id = str(
        message.author.id
    )

    if guild_id:

        if guild_id not in rank_mensagens:

            rank_mensagens[
                guild_id
            ] = {}

        if user_id not in rank_mensagens[guild_id]:

            rank_mensagens[
                guild_id
            ][user_id] = 0

        # Adiciona mensagem
        rank_mensagens[
            guild_id
        ][user_id] += 1

        # Verifica TOP 10 e TOP 1
        await verificar_ranking(
            message.guild
        )

        # Salva ranking
        salvar_json(
            RANK_FILE,
            rank_mensagens
        )

    # -----------------------------------------------------
    # REMOVE AFK QUANDO A PESSOA VOLTA
    # -----------------------------------------------------

    if guild_id:

        chave_afk = (
            f"{guild_id}_{user_id}"
        )

        if chave_afk in afk_usuarios:

            del afk_usuarios[
                chave_afk
            ]

            salvar_json(
                AFK_FILE,
                afk_usuarios
            )

            try:

                aviso = await message.channel.send(
                    f"👋 Bem-vindo de volta, "
                    f"{message.author.mention}!\n"
                    f"Seu AFK foi removido."
                )

                await asyncio.sleep(
                    5
                )

                try:

                    await aviso.delete()

                except:

                    pass

            except:

                pass

    # -----------------------------------------------------
    # AVISA QUANDO MENCIONAM ALGUÉM AFK
    # -----------------------------------------------------

    if guild_id:

        for membro in message.mentions:

            chave_mencionado = (
                f"{guild_id}_{membro.id}"
            )

            if chave_mencionado in afk_usuarios:

                dados = afk_usuarios[
                    chave_mencionado
                ]

                motivo = dados.get(
                    "motivo",
                    "AFK"
                )

                desde = dados.get(
                    "desde",
                    int(time.time())
                )

                await message.channel.send(
                    f"💤 **{membro.display_name}** "
                    f"está AFK.\n"
                    f"📝 Motivo: **{motivo}**\n"
                    f"⏰ Desde: "
                    f"<t:{desde}:R>"
                )

    # -----------------------------------------------------
    # PROCESSA COMANDOS
    # -----------------------------------------------------

    await bot.process_commands(
        message
    )


# =========================================================
# EDITOR DE EMBED
# =========================================================

class EmbedEditorView(discord.ui.View):

    def __init__(self, autor):

        super().__init__(
            timeout=600
        )

        self.autor = autor

        self.titulo = ""
        self.descricao = ""
        self.imagem = ""
        self.thumbnail = ""
        self.cor = discord.Color.blurple()
        self.rodape = ""

    async def verificar_usuario(
        self,
        interaction
    ):

        if interaction.user.id != self.autor.id:

            await interaction.response.send_message(
                "❌ Apenas quem criou este Embed pode editá-lo.",
                ephemeral=True
            )

            return False

        return True

    def criar_embed(self):

        embed = discord.Embed(
            color=self.cor
        )

        if self.titulo:

            embed.title = self.titulo

        if self.descricao:

            embed.description = self.descricao

        if self.imagem:

            embed.set_image(
                url=self.imagem
            )

        if self.thumbnail:

            embed.set_thumbnail(
                url=self.thumbnail
            )

        if self.rodape:

            embed.set_footer(
                text=self.rodape
            )

        return embed

    def criar_painel(self):

        embed = discord.Embed(
            title="🎨 Editor de Embed",
            description=(
                "Use os botões abaixo para montar seu Embed.\n\n"
                f"**Título:** "
                f"{self.titulo if self.titulo else 'Não definido'}\n"
                f"**Descrição:** "
                f"{'Definida' if self.descricao else 'Não definida'}\n"
                f"**Imagem:** "
                f"{'✅' if self.imagem else '❌'}\n"
                f"**Thumbnail:** "
                f"{'✅' if self.thumbnail else '❌'}\n"
                f"**Cor:** "
                f"`#{self.cor.value:06X}`\n"
                f"**Rodapé:** "
                f"{self.rodape if self.rodape else 'Não definido'}"
            ),
            color=self.cor
        )

        embed.set_footer(
            text="Somente você pode editar este painel."
        )

        return embed

    @discord.ui.button(
        label="Título",
        emoji="✏️",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def titulo_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.send_modal(
            TituloModal(self)
        )

    @discord.ui.button(
        label="Descrição",
        emoji="📝",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def descricao_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.send_modal(
            DescricaoModal(self)
        )

    @discord.ui.button(
        label="Imagem",
        emoji="🖼️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def imagem_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.send_modal(
            ImagemModal(self)
        )

    @discord.ui.button(
        label="Thumbnail",
        emoji="🔹",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def thumbnail_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.send_modal(
            ThumbnailModal(self)
        )

    @discord.ui.button(
        label="Cor",
        emoji="🎨",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def cor_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.send_modal(
            CorModal(self)
        )

    @discord.ui.button(
        label="Rodapé",
        emoji="👣",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def rodape_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.send_modal(
            RodapeModal(self)
        )

    @discord.ui.button(
        label="Pré-visualizar",
        emoji="👀",
        style=discord.ButtonStyle.success,
        row=3
    )
    async def preview_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        embed = self.criar_embed()

        if not self.titulo and not self.descricao:

            embed.description = (
                "⚠️ Seu Embed ainda está vazio."
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="ENVIAR",
        emoji="📤",
        style=discord.ButtonStyle.success,
        row=3
    )
    async def enviar_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        if not self.titulo and not self.descricao:

            await interaction.response.send_message(
                "❌ Adicione pelo menos um título ou uma descrição.",
                ephemeral=True
            )

            return

        await interaction.channel.send(
            embed=self.criar_embed()
        )

        await interaction.response.edit_message(
            content="✅ **Embed enviado com sucesso!**",
            embed=None,
            view=None
        )

        self.stop()

    @discord.ui.button(
        label="CANCELAR",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        row=3
    )
    async def cancelar_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar_usuario(
            interaction
        ):
            return

        await interaction.response.edit_message(
            content="🗑️ **Editor de Embed cancelado.**",
            embed=None,
            view=None
        )

        self.stop()


# =========================================================
# MODAIS DO EMBED
# =========================================================

class TituloModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(
            title="✏️ Editar Título"
        )

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Título",
            placeholder="Digite o título...",
            default=editor.titulo,
            required=False,
            max_length=256
        )

        self.add_item(
            self.campo
        )

    async def on_submit(
        self,
        interaction
    ):

        self.editor.titulo = (
            self.campo.value.strip()
        )

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class DescricaoModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(
            title="📝 Editar Descrição"
        )

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Descrição",
            placeholder="Digite a descrição...",
            default=editor.descricao,
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.add_item(
            self.campo
        )

    async def on_submit(
        self,
        interaction
    ):

        self.editor.descricao = (
            self.campo.value.strip()
        )

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class ImagemModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(
            title="🖼️ Imagem"
        )

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="URL da imagem",
            placeholder="https://exemplo.com/imagem.png",
            default=editor.imagem,
            required=False
        )

        self.add_item(
            self.campo
        )

    async def on_submit(
        self,
        interaction
    ):

        self.editor.imagem = (
            self.campo.value.strip()
        )

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class ThumbnailModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(
            title="🔹 Thumbnail"
        )

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="URL da Thumbnail",
            placeholder="https://exemplo.com/imagem.png",
            default=editor.thumbnail,
            required=False
        )

        self.add_item(
            self.campo
        )

    async def on_submit(
        self,
        interaction
    ):

        self.editor.thumbnail = (
            self.campo.value.strip()
        )

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class CorModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(
            title="🎨 Cor"
        )

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Cor HEX",
            placeholder="#5865F2",
            default=f"#{editor.cor.value:06X}",
            required=True,
            max_length=7
        )

        self.add_item(
            self.campo
        )

    async def on_submit(
        self,
        interaction
    ):

        valor = (
            self.campo.value
            .strip()
            .replace("#", "")
        )

        try:

            numero = int(
                valor,
                16
            )

            if numero > 0xFFFFFF:
                raise ValueError

            self.editor.cor = discord.Color(
                numero
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ Cor inválida! Exemplo: `#5865F2`",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class RodapeModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(
            title="👣 Rodapé"
        )

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Texto do rodapé",
            placeholder="Digite o texto...",
            default=editor.rodape,
            required=False,
            max_length=2048
        )

        self.add_item(
            self.campo
        )

    async def on_submit(
        self,
        interaction
    ):

        self.editor.rodape = (
            self.campo.value.strip()
        )

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


# =========================================================
# .EMBED
# =========================================================

@bot.command(name="embed")
@commands.has_permissions(
    manage_messages=True
)
async def embed_command(ctx):

    view = EmbedEditorView(
        ctx.author
    )

    await ctx.send(
        embed=view.criar_painel(),
        view=view
    )


# =========================================================
# .AV
# =========================================================

@bot.command(name="av")
async def avatar(
    ctx,
    membro: discord.Member = None
):

    membro = membro or ctx.author

    embed = discord.Embed(
        title=f"🖼️ Avatar de {membro.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_image(
        url=membro.display_avatar.url
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .BN
# =========================================================

@bot.command(name="bn")
async def banner(
    ctx,
    membro: discord.Member = None
):

    membro = membro or ctx.author

    usuario = await bot.fetch_user(
        membro.id
    )

    if usuario.banner is None:

        await ctx.send(
            f"❌ **{membro.display_name}** "
            "não possui um banner."
        )

        return

    embed = discord.Embed(
        title=f"🖼️ Banner de {membro.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_image(
        url=usuario.banner.url
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .USER
# =========================================================

@bot.command(name="user")
async def informacoes_usuario(
    ctx,
    membro: discord.Member = None
):

    membro = membro or ctx.author

    embed = discord.Embed(
        title=f"👤 Informações de {membro.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(
        url=membro.display_avatar.url
    )

    embed.add_field(
        name="👤 Usuário",
        value=str(membro),
        inline=True
    )

    embed.add_field(
        name="🆔 ID",
        value=f"`{membro.id}`",
        inline=True
    )

    embed.add_field(
        name="📅 Conta criada",
        value=discord.utils.format_dt(
            membro.created_at,
            style="F"
        ),
        inline=False
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .SERVER
# =========================================================

@bot.command(name="server")
async def informacoes_servidor(ctx):

    servidor = ctx.guild

    embed = discord.Embed(
        title=f"🏠 {servidor.name}",
        color=discord.Color.blurple()
    )

    if servidor.icon:

        embed.set_thumbnail(
            url=servidor.icon.url
        )

    embed.add_field(
        name="👥 Membros",
        value=str(
            servidor.member_count
        ),
        inline=True
    )

    embed.add_field(
        name="💬 Canais",
        value=str(
            len(servidor.channels)
        ),
        inline=True
    )

    embed.add_field(
        name="🎭 Cargos",
        value=str(
            len(servidor.roles)
        ),
        inline=True
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .PING
# =========================================================

@bot.command(name="ping")
async def ping(ctx):

    latencia = round(
        bot.latency * 1000
    )

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: **{latencia}ms**",
        color=discord.Color.green()
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .CL
# =========================================================

@bot.command(name="cl")
async def limpar_mensagens(ctx):

    usuario_id = ctx.author.id

    permissoes = ctx.channel.permissions_for(
        ctx.guild.me
    )

    if not permissoes.manage_messages:

        await ctx.send(
            "❌ Eu preciso da permissão "
            "**Gerenciar Mensagens** neste canal."
        )

        return

    agora = asyncio.get_running_loop().time()

    if usuario_id in cl_cooldown:

        restante = (
            cl_cooldown[usuario_id]
            - agora
        )

        if restante > 0:

            minutos = int(
                restante // 60
            )

            segundos = int(
                restante % 60
            )

            if minutos:

                tempo = (
                    f"{minutos}min "
                    f"{segundos}s"
                )

            else:

                tempo = f"{segundos}s"

            await ctx.send(
                f"⏳ {ctx.author.mention}, aguarde "
                f"**{tempo}** para usar `.cl` novamente."
            )

            return

        cl_cooldown.pop(
            usuario_id,
            None
        )

    if cl_ativo.get(
        usuario_id,
        False
    ):

        await ctx.send(
            "⚠️ Você já possui um CL em andamento."
        )

        return

    cl_ativo[usuario_id] = True

    try:

        mensagens = []

        async for mensagem in ctx.channel.history(
            limit=100
        ):

            if mensagem.author.id == usuario_id:

                mensagens.append(
                    mensagem
                )

        if not mensagens:

            await ctx.send(
                "❌ Não encontrei suas mensagens recentes."
            )

            return

        ids_mensagens = {
            mensagem.id
            for mensagem in mensagens
        }

        def verificar(mensagem):

            return mensagem.id in ids_mensagens

        try:

            apagadas = await ctx.channel.purge(
                limit=100,
                check=verificar,
                bulk=True
            )

        except discord.HTTPException as erro:

            if erro.status == 429:

                retry_after = getattr(
                    erro,
                    "retry_after",
                    2
                )

                await asyncio.sleep(
                    retry_after
                )

                apagadas = await ctx.channel.purge(
                    limit=100,
                    check=verificar,
                    bulk=True
                )

            else:

                raise

        total = len(
            apagadas
        )

        if total > 0:

            cl_cooldown[
                usuario_id
            ] = (
                asyncio.get_running_loop().time()
                + CL_COOLDOWN
            )

        await ctx.send(
            f"🧹 **CL concluído!**\n"
            f"**{total}** mensagens suas foram apagadas."
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Não tenho permissão para apagar "
            "mensagens neste canal."
        )

    except discord.HTTPException as erro:

        print(
            f"⚠️ Erro HTTP no CL: {erro}"
        )

        await ctx.send(
            "❌ O Discord recusou a operação. "
            "Tente novamente mais tarde."
        )

    except Exception as erro:

        print(
            f"⚠️ Erro no CL: {erro}"
        )

        await ctx.send(
            "❌ Ocorreu um erro ao executar o CL."
        )

    finally:

        cl_ativo.pop(
            usuario_id,
            None
        )


# =========================================================
# .CC
# =========================================================

@bot.command(name="cc")
async def cancelar_cl(ctx):

    usuario_id = ctx.author.id

    if not cl_ativo.get(
        usuario_id,
        False
    ):

        await ctx.send(
            "ℹ️ Você não possui nenhum CL em andamento."
        )

        return

    cl_ativo[usuario_id] = False

    await ctx.send(
        "🛑 **CL cancelado!**"
    )


# =========================================================
# .NUKE
# =========================================================

@bot.command(name="nuke")
@commands.has_permissions(
    manage_channels=True
)
async def nuke(ctx):

    canal = ctx.channel

    try:

        novo_canal = await canal.clone(
            reason=f"Nuke solicitado por {ctx.author}"
        )

        await canal.delete(
            reason=f"Nuke solicitado por {ctx.author}"
        )

        await novo_canal.send(
            f"💥 **Canal resetado!**\n"
            f"Solicitado por {ctx.author.mention}."
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Preciso da permissão "
            "**Gerenciar Canais**."
        )

    except discord.HTTPException as erro:

        print(
            f"⚠️ Erro no NUKE: {erro}"
        )


# =========================================================
# .AFK
# =========================================================

@bot.command(name="afk")
async def afk(
    ctx,
    *,
    motivo="AFK"
):

    if ctx.guild is None:

        await ctx.send(
            "❌ Este comando só funciona em servidores."
        )

        return

    chave = (
        f"{ctx.guild.id}_{ctx.author.id}"
    )

    afk_usuarios[chave] = {
        "motivo": motivo,
        "desde": int(
            time.time()
        )
    }

    salvar_json(
        AFK_FILE,
        afk_usuarios
    )

    await ctx.send(
        f"💤 {ctx.author.mention} agora está AFK.\n"
        f"📝 Motivo: **{motivo}**"
    )


# =========================================================
# .RANK
# =========================================================

@bot.command(name="rank")
async def rank(
    ctx,
    membro: discord.Member = None
):

    if ctx.guild is None:
        return

    guild_id = str(
        ctx.guild.id
    )

    dados = rank_mensagens.get(
        guild_id,
        {}
    )

    if membro:

        user_id = str(
            membro.id
        )

        mensagens = dados.get(
            user_id,
            0
        )

        lista = sorted(
            dados.items(),
            key=lambda x: x[1],
            reverse=True
        )

        posicao = 0

        for i, (uid, quantidade) in enumerate(
            lista,
            start=1
        ):

            if uid == user_id:

                posicao = i
                break

        embed = discord.Embed(
            title=f"🏆 Rank de {membro.display_name}",
            color=discord.Color.gold()
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        embed.add_field(
            name="💬 Mensagens",
            value=f"**{mensagens}**",
            inline=True
        )

        embed.add_field(
            name="📊 Posição",
            value=(
                f"**#{posicao}**"
                if posicao
                else "Sem posição"
            ),
            inline=True
        )

        await ctx.send(
            embed=embed
        )

        return

    # -----------------------------------------------------
    # RANKING GERAL
    # -----------------------------------------------------

    lista = sorted(
        dados.items(),
        key=lambda x: x[1],
        reverse=True
    )

    if not lista:

        await ctx.send(
            "📊 Ainda não existem mensagens registradas."
        )

        return

    embed = discord.Embed(
        title=f"🏆 Ranking da Semana — {ctx.guild.name}",
        description=(
            "📅 O ranking é resetado toda segunda-feira "
            "às 00:00."
        ),
        color=discord.Color.gold()
    )

    linhas = []

    for posicao, (user_id, quantidade) in enumerate(
        lista[:10],
        start=1
    ):

        membro = ctx.guild.get_member(
            int(user_id)
        )

        if membro:

            nome = membro.display_name

        else:

            nome = f"Usuário {user_id}"

        if posicao == 1:

            medalha = "🥇"

        elif posicao == 2:

            medalha = "🥈"

        elif posicao == 3:

            medalha = "🥉"

        else:

            medalha = f"`#{posicao}`"

        linhas.append(
            f"{medalha} **{nome}** — "
            f"💬 {quantidade}"
        )

    embed.description += (
        "\n\n"
        + "\n".join(linhas)
    )

    embed.set_footer(
        text="Top 10 por quantidade de mensagens"
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# MENU DO ADD FIG
# =========================================================

class AddFigView(discord.ui.View):

    def __init__(self, autor):

        super().__init__(
            timeout=120
        )

        self.autor = autor

    async def verificar(
        self,
        interaction
    ):

        if interaction.user.id != self.autor.id:

            await interaction.response.send_message(
                "❌ Apenas quem abriu o menu pode usar estas opções.",
                ephemeral=True
            )

            return False

        return True

    @discord.ui.button(
        label="Adicionar por URL",
        emoji="🔗",
        style=discord.ButtonStyle.primary
    )
    async def url_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar(
            interaction
        ):
            return

        await interaction.response.send_modal(
            AddFigURLModal()
        )

    @discord.ui.button(
        label="Fechar",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def fechar_button(
        self,
        interaction,
        button
    ):

        if not await self.verificar(
            interaction
        ):
            return

        await interaction.response.edit_message(
            content="❌ Menu fechado.",
            embed=None,
            view=None
        )

        self.stop()


class AddFigURLModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="🖼️ Adicionar Figurinha"
        )

        self.nome = discord.ui.TextInput(
            label="Nome da figurinha",
            placeholder="Exemplo: t7",
            max_length=30,
            required=True
        )

        self.url = discord.ui.TextInput(
            label="URL da figurinha",
            placeholder="https://exemplo.com/figurinha.png",
            required=True
        )

        self.descricao = discord.ui.TextInput(
            label="Descrição",
            placeholder="Minha figurinha",
            required=False,
            max_length=100
        )

        self.emoji = discord.ui.TextInput(
            label="Emoji associado",
            placeholder="😎",
            default="😎",
            required=True,
            max_length=2
        )

        self.add_item(
            self.nome
        )

        self.add_item(
            self.url
        )

        self.add_item(
            self.descricao
        )

        self.add_item(
            self.emoji
        )

    async def on_submit(
        self,
        interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ Use isso dentro de um servidor.",
                ephemeral=True
            )

            return

        permissoes = guild.me.guild_permissions

        if not permissoes.manage_emojis:

            await interaction.response.send_message(
                "❌ Eu preciso da permissão "
                "**Gerenciar Expressões**.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            async with aiohttp.ClientSession() as session:

                async with session.get(
                    self.url.value,
                    timeout=20
                ) as resposta:

                    if resposta.status != 200:

                        await interaction.followup.send(
                            "❌ Não consegui baixar a figurinha.",
                            ephemeral=True
                        )

                        return

                    dados = await resposta.read()

            arquivo = discord.File(
                fp=__import__(
                    "io"
                ).BytesIO(dados),
                filename="figurinha.png"
            )

            nova_fig = await guild.create_sticker(
                name=self.nome.value,
                description=(
                    self.descricao.value
                    or "Figurinha adicionada pelo bot"
                ),
                emoji=self.emoji.value,
                file=arquivo,
                reason=f"Adicionada por {interaction.user}"
            )

            await interaction.followup.send(
                f"✅ **Figurinha adicionada!**\n\n"
                f"Nome: `{nova_fig.name}`",
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ Não tenho permissão para adicionar "
                "figurinhas neste servidor.",
                ephemeral=True
            )

        except discord.HTTPException as erro:

            await interaction.followup.send(
                "❌ O Discord recusou a figurinha.\n"
                "Verifique se o arquivo/URL é válido e "
                "se o servidor pode receber mais figurinhas.",
                ephemeral=True
            )

            print(
                f"⚠️ Erro no ADD FIG: {erro}"
            )

        except Exception as erro:

            await interaction.followup.send(
                "❌ Ocorreu um erro ao adicionar a figurinha.",
                ephemeral=True
            )

            print(
                f"⚠️ Erro no ADD FIG: {erro}"
            )


# =========================================================
# .ADDFIG
# =========================================================

@bot.command(name="addfig")
@commands.has_permissions(
    manage_emojis=True
)
async def addfig(ctx):

    embed = discord.Embed(
        title="🖼️ Adicionar Figurinha",
        description=(
            "Use o menu abaixo para adicionar "
            "uma figurinha rapidamente.\n\n"
            "🔗 **Adicionar por URL**\n"
            "Informe a URL direta da imagem "
            "da figurinha."
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(
        embed=embed,
        view=AddFigView(
            ctx.author
        )
    )


# =========================================================
# .ADDEMOJI
# =========================================================

@bot.command(name="addemoji")
@commands.has_permissions(
    manage_emojis=True
)
async def adicionar_emoji(
    ctx,
    emoji: discord.PartialEmoji = None
):

    if emoji is None:

        await ctx.send(
            "❌ Você precisa informar um emoji personalizado.\n\n"
            "**Exemplo:**\n"
            "`.addemoji <:emoji:123456789>`\n\n"
            "Animado:\n"
            "`.addemoji <a:emoji:123456789>`"
        )

        return

    if ctx.guild is None:

        await ctx.send(
            "❌ Este comando só pode ser usado "
            "dentro de um servidor."
        )

        return

    permissoes = ctx.guild.me.guild_permissions

    if not permissoes.manage_emojis:

        await ctx.send(
            "❌ Eu não tenho a permissão "
            "**Gerenciar Expressões**."
        )

        return

    try:

        imagem = await emoji.read()

        novo_emoji = await ctx.guild.create_custom_emoji(
            name=emoji.name,
            image=imagem,
            reason=f"Adicionado por {ctx.author}"
        )

        await ctx.send(
            f"✅ **Emoji adicionado com sucesso!**\n"
            f"Nome: `{novo_emoji.name}`\n"
            f"Emoji: {novo_emoji}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Não tenho permissão para "
            "adicionar emojis."
        )

    except discord.HTTPException as erro:

        print(
            f"⚠️ Erro ao adicionar emoji: {erro}"
        )

        await ctx.send(
            "❌ Não foi possível adicionar o emoji."
        )

    except Exception as erro:

        print(
            f"⚠️ Erro no ADD EMOJI: {erro}"
        )

        await ctx.send(
            "❌ Ocorreu um erro ao adicionar o emoji."
        )


# =========================================================
# .8BALL
# =========================================================

@bot.command(name="8ball")
async def bola_8(
    ctx,
    *,
    pergunta=None
):

    if not pergunta:

        await ctx.send(
            "❌ Faça uma pergunta.\n"
            "Exemplo: `.8ball Vou ficar rico?`"
        )

        return

    respostas = [
        "🎱 Sim!",
        "🎱 Com certeza!",
        "🎱 Provavelmente.",
        "🎱 Talvez.",
        "🎱 Não.",
        "🎱 Acho que não.",
        "🎱 Definitivamente não.",
        "🎱 Não posso responder isso.",
        "🎱 O futuro dirá."
    ]

    embed = discord.Embed(
        title="🎱 8 Ball",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="❓ Pergunta",
        value=pergunta,
        inline=False
    )

    embed.add_field(
        name="🔮 Resposta",
        value=random.choice(
            respostas
        ),
        inline=False
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .HELP
# =========================================================

@bot.command(name="help")
async def ajuda(ctx):

    embed = discord.Embed(
        title="📚 Central de Comandos",
        description=(
            "Confira os comandos disponíveis "
            "no T7 | Community."
        ),
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🎨 EMBEDS",
        value=(
            "`.embed` — Editor visual de Embed."
        ),
        inline=False
    )

    embed.add_field(
        name="👤 PERFIL",
        value=(
            "`.av [@usuário]` — Avatar\n"
            "`.bn [@usuário]` — Banner\n"
            "`.user [@usuário]` — Informações"
        ),
        inline=False
    )

    embed.add_field(
        name="🏠 SERVIDOR",
        value=(
            "`.server` — Informações\n"
            "`.ping` — Latência"
        ),
        inline=False
    )

    embed.add_field(
        name="🧹 MODERAÇÃO",
        value=(
            "`.cl` — Apaga até 100 mensagens suas\n"
            "`.cc` — Cancela CL\n"
            "`.nuke` — Reinicia o canal"
        ),
        inline=False
    )

    embed.add_field(
        name="💤 AFK",
        value=(
            "`.afk` — Fica AFK\n"
            "`.afk motivo` — Define motivo"
        ),
        inline=False
    )

    embed.add_field(
        name="🏆 RANKING SEMANAL",
        value=(
            "`.rank` — Ranking da semana\n"
            "`.rank @usuário` — Rank individual\n"
            "🔄 Reset toda segunda às 00:00\n"
            "⭐ TOP 10 recebem destaque\n"
            "👑 TOP 1 recebe cargo automaticamente"
        ),
        inline=False
    )

    embed.add_field(
        name="😀 EMOJIS / FIGURINHAS",
        value=(
            "`.addemoji <:emoji:ID>` — Adiciona emoji\n"
            "`.addfig` — Menu de figurinhas"
        ),
        inline=False
    )

    embed.add_field(
        name="🎱 DIVERSÃO",
        value=(
            "`.8ball pergunta` — Pergunte à bola 8"
        ),
        inline=False
    )

    embed.set_footer(
        text=f"Prefixo: {PREFIXO}"
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# ERROS
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Você não possui permissão "
            "para usar este comando."
        )

        return

    if isinstance(
        error,
        commands.BotMissingPermissions
    ):

        await ctx.send(
            "❌ Eu não tenho as permissões necessárias."
        )

        return

    if isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Não encontrei esse usuário."
        )

        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Está faltando um argumento "
            "nesse comando."
        )

        return

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Valor inválido. "
            "Confira o formato do comando."
        )

        return

    print(
        f"⚠️ Erro: {error}"
    )


# =========================================================
# INICIAR BOT
# =========================================================

if not TOKEN:

    print(
        "❌ ERRO: DISCORD_TOKEN não foi encontrado."
    )

else:

    bot.run(TOKEN)
