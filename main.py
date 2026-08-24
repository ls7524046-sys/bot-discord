import discord
import random
import asyncio
import os

from discord.ext import commands


# =========================================================
# CONFIGURAÇÕES
# =========================================================

TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIXO = "."


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

# Usuários que estão executando um CL
cl_ativo = {}

# Cooldown individual de cada usuário
cl_cooldown = {}

# 10 minutos
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

    # -----------------------------------------------------
    # TÍTULO
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # DESCRIÇÃO
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # IMAGEM
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # THUMBNAIL
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # COR
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # RODAPÉ
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # PRÉ-VISUALIZAR
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # ENVIAR
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CANCELAR
    # -----------------------------------------------------

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
# MODAL - TÍTULO
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

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.titulo = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


# =========================================================
# MODAL - DESCRIÇÃO
# =========================================================

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

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.descricao = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


# =========================================================
# MODAL - IMAGEM
# =========================================================

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

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.imagem = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


# =========================================================
# MODAL - THUMBNAIL
# =========================================================

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

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        self.editor.thumbnail = self.campo.value.strip()

        await interaction.response.edit_message(
            embed=self.editor.criar_painel(),
            view=self.editor
        )


# =========================================================
# MODAL - COR
# =========================================================

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

        self.add_item(self.campo)

    async def on_submit(self, interaction):

        valor = self.campo.value.strip().replace(
            "#",
            ""
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


# =========================================================
# MODAL - RODAPÉ
# =========================================================

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
async def limpar_mensagens(
    ctx,
    quantidade: int = 5
):

    usuario_id = ctx.author.id

    # -----------------------------------------------------
    # VERIFICA PERMISSÃO DO BOT
    # -----------------------------------------------------

    permissoes = ctx.channel.permissions_for(
        ctx.guild.me
    )

    if not permissoes.manage_messages:

        await ctx.send(
            "❌ Eu preciso da permissão "
            "**Gerenciar Mensagens** neste canal."
        )

        return

    # -----------------------------------------------------
    # LIMITE DE 1 ATÉ 10
    # -----------------------------------------------------

    if quantidade < 1 or quantidade > 10:

        await ctx.send(
            "❌ Você pode apagar de **1 até 10 mensagens**."
        )

        return

    # -----------------------------------------------------
    # COOLDOWN INDIVIDUAL
    # -----------------------------------------------------

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

            if minutos > 0:

                tempo = (
                    f"{minutos}min "
                    f"{segundos}s"
                )

            else:

                tempo = f"{segundos}s"

            await ctx.send(
                f"⏳ {ctx.author.mention}, aguarde "
                f"**{tempo}** para usar o `.cl` novamente."
            )

            return

        # Cooldown expirou
        cl_cooldown.pop(
            usuario_id,
            None
        )

    # -----------------------------------------------------
    # EVITA DOIS CL AO MESMO TEMPO
    # -----------------------------------------------------

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

        # -------------------------------------------------
        # PROCURA AS MENSAGENS DO USUÁRIO
        # -------------------------------------------------

        mensagens = []

        async for mensagem in ctx.channel.history(
            limit=100
        ):

            if mensagem.author.id == usuario_id:

                mensagens.append(
                    mensagem
                )

                if len(mensagens) >= quantidade:
                    break

        # -------------------------------------------------
        # NENHUMA MENSAGEM
        # -------------------------------------------------

        if not mensagens:

            await ctx.send(
                "❌ Não encontrei suas mensagens recentes."
            )

            return

        # -------------------------------------------------
        # GUARDA OS IDs
        # -------------------------------------------------

        ids_mensagens = {
            mensagem.id
            for mensagem in mensagens
        }

        # -------------------------------------------------
        # FILTRO DO PURGE
        # -----------------------------------------------------

        def verificar(mensagem):

            return mensagem.id in ids_mensagens

        # -------------------------------------------------
        # PURGE
        # -------------------------------------------------

        try:

            apagadas = await ctx.channel.purge(
                limit=100,
                check=verificar,
                bulk=True
            )

        except discord.HTTPException as erro:

            # -------------------------------------------------
            # RATE LIMIT
            # -------------------------------------------------

            if erro.status == 429:

                retry_after = getattr(
                    erro,
                    "retry_after",
                    2
                )

                print(
                    f"⚠️ Rate limit no CL. "
                    f"Aguardando {retry_after:.2f}s."
                )

                await asyncio.sleep(
                    retry_after
                )

                try:

                    apagadas = await ctx.channel.purge(
                        limit=100,
                        check=verificar,
                        bulk=True
                    )

                except discord.HTTPException:

                    await ctx.send(
                        "⚠️ O Discord aplicou um rate limit. "
                        "Tente novamente daqui a pouco."
                    )

                    return

            else:

                raise

        # -------------------------------------------------
        # QUANTIDADE APAGADA
        # -------------------------------------------------

        total_apagadas = len(
            apagadas
        )

        # -------------------------------------------------
        # COOLDOWN
        # -------------------------------------------------

        if total_apagadas > 0:

            cl_cooldown[usuario_id] = (
                asyncio.get_running_loop().time()
                + CL_COOLDOWN
            )

        # -------------------------------------------------
        # RESULTADO
        # -------------------------------------------------

        await ctx.send(
            f"🧹 **CL concluído!**\n"
            f"**{total_apagadas}** mensagens foram apagadas."
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
            "❌ Ocorreu um erro do Discord ao "
            "tentar apagar as mensagens."
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
    emoji: discord.PartialEmoji = None
):

    # -----------------------------------------------------
    # SEM EMOJI
    # -----------------------------------------------------

    if emoji is None:

        await ctx.send(
            "❌ Você precisa informar um emoji personalizado.\n\n"
            "**Exemplo:**\n"
            "`.addemoji <:emoji:123456789>`\n\n"
            "Emoji animado:\n"
            "`.addemoji <a:emoji:123456789>`"
        )

        return

    # -----------------------------------------------------
    # VERIFICA SERVIDOR
    # -----------------------------------------------------

    if ctx.guild is None:

        await ctx.send(
            "❌ Este comando só pode ser usado "
            "dentro de um servidor."
        )

        return

    # -----------------------------------------------------
    # VERIFICA PERMISSÃO DO BOT
    # -----------------------------------------------------

    permissoes = ctx.guild.me.guild_permissions

    if not permissoes.manage_emojis:

        await ctx.send(
            "❌ Eu não tenho a permissão "
            "**Gerenciar Expressões** neste servidor."
        )

        return

    # -----------------------------------------------------
    # ADICIONA O EMOJI
    # -----------------------------------------------------

    try:

        imagem = await emoji.read()

        novo_emoji = await ctx.guild.create_custom_emoji(
            name=emoji.name,
            image=imagem,
            reason=f"Adicionado por {ctx.author}"
        )

        await ctx.send(
            f"✅ **Emoji adicionado com sucesso!**\n\n"
            f"Nome: `{novo_emoji.name}`\n"
            f"Emoji: {novo_emoji}"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ Não tenho permissão para "
            "adicionar emojis neste servidor."
        )

    except discord.HTTPException as erro:

        print(
            f"⚠️ Erro ao adicionar emoji: {erro}"
        )

        await ctx.send(
            "❌ Não foi possível adicionar o emoji.\n"
            f"Erro: `{erro}`"
        )

    except Exception as erro:

        print(
            f"⚠️ Erro ao adicionar emoji: {erro}"
        )

        await ctx.send(
            "❌ Ocorreu um erro ao tentar adicionar o emoji."
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
            "`.embed` — Abre o editor visual de Embed."
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
            "Adiciona um emoji personalizado."
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
# TRATAMENTO DE ERROS
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    # -----------------------------------------------------
    # COMANDO NÃO EXISTE
    # -----------------------------------------------------

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    # -----------------------------------------------------
    # USUÁRIO SEM PERMISSÃO
    # -----------------------------------------------------

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Você não possui permissão "
            "para usar este comando."
        )

        return

    # -----------------------------------------------------
    # BOT SEM PERMISSÃO
    # -----------------------------------------------------

    if isinstance(
        error,
        commands.BotMissingPermissions
    ):

        await ctx.send(
            "❌ Eu não tenho as permissões necessárias."
        )

        return

    # -----------------------------------------------------
    # MEMBRO NÃO ENCONTRADO
    # -----------------------------------------------------

    if isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Não encontrei esse usuário."
        )

        return

    # -----------------------------------------------------
    # ARGUMENTO OBRIGATÓRIO
    # -----------------------------------------------------

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        if error.param.name == "emoji":

            await ctx.send(
                "❌ Você precisa informar um emoji.\n\n"
                "**Exemplo:**\n"
                "`.addemoji <:emoji:123456789>`"
            )

            return

    # -----------------------------------------------------
    # ARGUMENTO INVÁLIDO
    # -----------------------------------------------------

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Valor inválido.\n"
            "Confira o formato do comando."
        )

        return

    # -----------------------------------------------------
    # OUTROS ERROS
    # -----------------------------------------------------

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
