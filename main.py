import discord
import random
import asyncio
from discord.ext import commands
import os

TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIXO = "."

# =========================================================
# CONFIGURAÇÕES
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIXO,
    intents=intents,
    help_command=None
)

# =========================================================
# CONFIGURAÇÕES DO CL
# =========================================================

cl_ativo = {}
cl_cooldown = {}

# 10 minutos em segundos
CL_COOLDOWN = 600


# =========================================================
# BOT ONLINE
# =========================================================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"✅ Bot online: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"📌 Prefixo: {PREFIXO}")
    print("=" * 50)


# =========================================================
# EDITOR DE EMBED
# =========================================================

class EmbedEditorView(discord.ui.View):

    def __init__(self, autor):

        super().__init__(timeout=600)

        self.autor = autor
        self.titulo = ""
        self.descricao = ""
        self.imagem = ""
        self.thumbnail = ""
        self.cor = discord.Color.blurple()
        self.rodape = ""

    async def verificar_usuario(self, interaction):

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
    async def titulo_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def descricao_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def imagem_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def thumbnail_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def cor_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def rodape_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def preview_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
            return

        embed = self.criar_embed()

        if not self.titulo and not self.descricao:

            embed.description = (
                "⚠️ Seu Embed ainda está vazio.\n"
                "Adicione um título ou descrição."
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
    async def enviar_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
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
    async def cancelar_button(self, interaction, button):

        if not await self.verificar_usuario(interaction):
            return

        await interaction.response.edit_message(
            content="🗑️ **Editor de Embed cancelado.**",
            embed=None,
            view=None
        )

        self.stop()


# =========================================================
# MODAIS
# =========================================================

class TituloModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(title="✏️ Editar Título")

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Título",
            placeholder="Digite o título...",
            default=editor.titulo,
            required=False,
            max_length=256
        )

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.titulo = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class DescricaoModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(title="📝 Editar Descrição")

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Descrição",
            placeholder="Digite a descrição...",
            default=editor.descricao,
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=4000
        )

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.descricao = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class ImagemModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(title="🖼️ Imagem")

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="URL da imagem",
            placeholder="https://exemplo.com/imagem.png",
            default=editor.imagem,
            required=False
        )

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.imagem = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class ThumbnailModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(title="🔹 Thumbnail")

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="URL da Thumbnail",
            placeholder="https://exemplo.com/imagem.png",
            default=editor.thumbnail,
            required=False
        )

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.thumbnail = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


class CorModal(discord.ui.Modal):

    def __init__(self, editor):

        super().__init__(title="🎨 Cor")

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Cor HEX",
            placeholder="#5865F2",
            default=f"#{editor.cor.value:06X}",
            required=True,
            max_length=7
        )

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        valor = self.campo.value.strip().replace("#", "")

        try:

            numero = int(valor, 16)

            if numero > 0xFFFFFF:
                raise ValueError

            self.editor.cor = discord.Color(numero)

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

        super().__init__(title="👣 Rodapé")

        self.editor = editor

        self.campo = discord.ui.TextInput(
            label="Texto do rodapé",
            placeholder="Digite o texto...",
            default=editor.rodape,
            required=False,
            max_length=2048
        )

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.rodape = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


# =========================================================
# .EMBED
# =========================================================

@bot.command(name="embed")
@commands.has_permissions(manage_messages=True)
async def embed_command(ctx):

    view = EmbedEditorView(ctx.author)

    await ctx.send(
        embed=view.criar_painel(),
        view=view
    )


# =========================================================
# .AV
# =========================================================

@bot.command(name="av")
async def avatar(ctx, membro: discord.Member = None):

    membro = membro or ctx.author

    embed = discord.Embed(
        title=f"🖼️ Avatar de {membro.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_image(
        url=membro.display_avatar.url
    )

    await ctx.send(embed=embed)


# =========================================================
# .BN
# =========================================================

@bot.command(name="bn")
async def banner(ctx, membro: discord.Member = None):

    membro = membro or ctx.author

    usuario = await bot.fetch_user(membro.id)

    if usuario.banner is None:

        await ctx.send(
            f"❌ **{membro.display_name}** não possui um banner."
        )

        return

    embed = discord.Embed(
        title=f"🖼️ Banner de {membro.display_name}",
        color=discord.Color.blurple()
    )

    embed.set_image(
        url=usuario.banner.url
    )

    await ctx.send(embed=embed)


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

    await ctx.send(embed=embed)


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
        value=str(servidor.member_count),
        inline=True
    )

    embed.add_field(
        name="💬 Canais",
        value=str(len(servidor.channels)),
        inline=True
    )

    embed.add_field(
        name="🎭 Cargos",
        value=str(len(servidor.roles)),
        inline=True
    )

    await ctx.send(embed=embed)


# =========================================================
# .PING
# =========================================================

@bot.command(name="ping")
async def ping(ctx):

    latencia = round(bot.latency * 1000)

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: **{latencia}ms**",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)


# =========================================================
# .CL
# =========================================================

@bot.command(name="cl")
async def limpar_mensagens(
    ctx,
    quantidade: int = 5
):

    usuario_id = ctx.author.id

    # =====================================================
    # VERIFICA PERMISSÃO DO BOT
    # =====================================================

    if not ctx.channel.permissions_for(
        ctx.guild.me
    ).manage_messages:

        await ctx.send(
            "❌ Eu não tenho a permissão "
            "**Gerenciar Mensagens** neste canal."
        )

        return

    # =====================================================
    # VERIFICA QUANTIDADE
    # =====================================================

    if quantidade < 1 or quantidade > 10:

        aviso = await ctx.send(
            "❌ Você pode apagar de **1 até 10 mensagens** por vez."
        )

        await aviso.delete(delay=5)

        return

    # =====================================================
    # VERIFICA COOLDOWN
    # =====================================================

    agora = asyncio.get_running_loop().time()

    if usuario_id in cl_cooldown:

        restante = cl_cooldown[usuario_id] - agora

        if restante > 0:

            minutos = int(restante // 60)
            segundos = int(restante % 60)

            if minutos > 0:

                tempo = f"{minutos}min {segundos}s"

            else:

                tempo = f"{segundos}s"

            aviso = await ctx.send(
                f"⏳ **Calma, {ctx.author.mention}!**\n\n"
                f"Você poderá usar o `.cl` novamente em "
                f"**{tempo}**."
            )

            await aviso.delete(delay=5)

            return

        cl_cooldown.pop(
            usuario_id,
            None
        )

    # =====================================================
    # VERIFICA SE JÁ TEM UM CL RODANDO
    # =====================================================

    if cl_ativo.get(usuario_id, False):

        aviso = await ctx.send(
            "⚠️ Você já possui um **CL** em andamento.\n"
            "Use `.cc` para cancelar."
        )

        await aviso.delete(delay=5)

        return

    # =====================================================
    # ATIVA O CL
    # =====================================================

    cl_ativo[usuario_id] = True

    mensagens = []

    try:

        # =================================================
        # PROCURA AS MENSAGENS DO USUÁRIO
        # =================================================

        async for mensagem in ctx.channel.history(
            limit=None
        ):

            if not cl_ativo.get(
                usuario_id,
                False
            ):
                break

            if mensagem.author.id == usuario_id:

                mensagens.append(
                    mensagem
                )

                if len(mensagens) >= quantidade:
                    break

        # =================================================
        # NENHUMA MENSAGEM
        # =================================================

        if not mensagens:

            aviso = await ctx.send(
                "❌ Não encontrei suas mensagens neste canal."
            )

            await aviso.delete(
                delay=5
            )

            return

        apagadas = 0

        # =================================================
        # APAGA AS MENSAGENS
        # =================================================

        for mensagem in mensagens:

            if not cl_ativo.get(
                usuario_id,
                False
            ):
                break

            try:

                await mensagem.delete()

                apagadas += 1

                # Intervalo para evitar rate limit
                await asyncio.sleep(0.8)

            except discord.NotFound:

                pass

            except discord.Forbidden:

                aviso = await ctx.send(
                    "❌ Não tenho permissão para apagar "
                    "mensagens neste canal."
                )

                await aviso.delete(
                    delay=5
                )

                return

            except discord.HTTPException as erro:

                # =================================================
                # RATE LIMIT
                # =================================================

                if erro.status == 429:

                    await asyncio.sleep(
                        2
                    )

                    try:

                        await mensagem.delete()

                        apagadas += 1

                    except discord.HTTPException:

                        pass

        # =================================================
        # CANCELADO
        # =================================================

        if not cl_ativo.get(
            usuario_id,
            False
        ):

            aviso = await ctx.send(
                f"🛑 **CL cancelado!**\n"
                f"**{apagadas}** mensagens foram apagadas."
            )

            await aviso.delete(
                delay=5
            )

            return

        # =================================================
        # CONCLUÍDO
        # =================================================

        aviso = await ctx.send(
            f"🧹 **CL concluído!**\n"
            f"**{apagadas}** mensagens foram apagadas."
        )

        await aviso.delete(
            delay=5
        )

        # =================================================
        # COOLDOWN DE 10 MINUTOS
        # =================================================

        cl_cooldown[usuario_id] = (
            asyncio.get_running_loop().time()
            + CL_COOLDOWN
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

        aviso = await ctx.send(
            "ℹ️ Você não possui nenhum **CL** em andamento."
        )

        await aviso.delete(
            delay=5
        )

        return

    cl_ativo[usuario_id] = False

    aviso = await ctx.send(
        "🛑 **CL cancelado!**"
    )

    await aviso.delete(
        delay=5
    )


# =========================================================
# .DADO
# =========================================================

@bot.command(name="dado")
async def dado(ctx):

    numero = random.randint(
        1,
        6
    )

    embed = discord.Embed(
        title="🎲 Dado",
        description=f"Você tirou **{numero}**!",
        color=discord.Color.blurple()
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# .COIN
# =========================================================

@bot.command(name="coin")
async def moeda(ctx):

    resultado = random.choice(
        [
            "Cara",
            "Coroa"
        ]
    )

    embed = discord.Embed(
        title="🪙 Cara ou Coroa",
        description=f"Resultado: **{resultado}**",
        color=discord.Color.gold()
    )

    await ctx.send(
        embed=embed
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
# .ADDEMOJI
# =========================================================

@bot.command(name="addemoji")
@commands.has_permissions(
    manage_emojis=True
)
async def adicionar_emoji(
    ctx,
    emoji: discord.PartialEmoji
):

    if not ctx.guild:

        await ctx.send(
            "❌ Este comando só pode ser usado "
            "dentro de um servidor."
        )

        return

    if not emoji.is_custom_emoji():

        await ctx.send(
            "❌ Você precisa enviar um "
            "**emoji personalizado**."
        )

        return

    try:

        imagem = await emoji.read()

        novo_emoji = await ctx.guild.create_custom_emoji(
            name=emoji.name,
            image=imagem
        )

        await ctx.send(
            f"✅ Emoji **{novo_emoji.name}** "
            f"adicionado com sucesso!\n"
            f"{novo_emoji}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Não tenho permissão para "
            "adicionar emojis neste servidor."
        )

    except discord.HTTPException as erro:

        await ctx.send(
            "❌ Não foi possível adicionar o emoji.\n"
            f"Erro: `{erro}`"
        )


# =========================================================
# .HELP
# =========================================================

@bot.command(name="help")
async def ajuda(ctx):

    embed = discord.Embed(
        title="📚 Central de Comandos",
        description=(
            "Confira abaixo todos os comandos "
            "disponíveis no bot."
        ),
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🎨 EMBEDS",
        value=(
            "`.embed` — Abre o editor visual "
            "de Embed com botões."
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
            "`.server` — Informações do servidor\n"
            "`.ping` — Latência do bot"
        ),
        inline=False
    )

    embed.add_field(
        name="🧹 LIMPEZA",
        value=(
            "`.cl` — Apaga 5 mensagens\n"
            "`.cl 1` até `.cl 10` — Escolhe a quantidade\n"
            "`.cc` — Cancela o CL\n"
            "⏱️ Cooldown: 10 minutos por usuário"
        ),
        inline=False
    )

    embed.add_field(
        name="🎮 DIVERSÃO",
        value=(
            "`.dado` — Rola um dado\n"
            "`.coin` — Cara ou coroa\n"
            "`.8ball pergunta` — Faz uma pergunta"
        ),
        inline=False
    )

    embed.add_field(
        name="😀 EMOJIS",
        value=(
            "`.addemoji <:emoji:ID>` — "
            "Adiciona um emoji personalizado "
            "de outro servidor."
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
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Valor inválido.\n"
            "Confira o formato do comando."
        )

        return

    print(
        f"⚠️ Erro: {error}"
    )


# =========================================================
# INICIAR
# =========================================================

bot.run(TOKEN)
