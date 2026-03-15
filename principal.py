import discord
import time
import threading
from discord import app_commands
from discord.ext import commands
import os
import datetime
import random
import asyncio
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.messages = True
# --- LISTA NEGRA GLOBAL ---
blacklist_ids = [1257319843875786843, 1425204611895263287, 1470798751399678124, 1382436321351696395, 967812550748172308, 1440444282153599089, 962474342095159316, 1395678169402445825, 1059382739498975295, 1473445540233478194, 1070385717211037796, 1021826215864189011, 1469787885820706876, 1414048184505860291, 1476678862678134837, 1393705382202839071, 952798822990508072, 1371348468337213521, 1173432515915165701, 1460375341884506259, 974092263800070144, 1374836732889010209, 1276693279055810651, 1363685756886974634, 1411860199056216074, 1477521161301790872, 1343037309943156850, 1122637301701427210, 1475956609120338109, 1246617016996069417, 1325875339804676192, 1035349110280163419, 1193756073966973028, 1347746512712761435, 1460745639754469581, 1223150802999316510, 981974769622724678, 1245542371165470793, 1459215951131054151, 1444127973958488156, 1205115475319853117, 959310198445572127, 1441941259554914305, 1478253953106841622, 1076576937947963493, 1269400106151706679, 1441116288587010239]

class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)


    async def setup_hook(self):
        await self.tree.sync()
        print("✅ DUCK SECURITY: ALL COMMANDS SYNCED IN ENGLISH")


bot = MyBot()

# Paso 1: Base de datos temporal para los canales de logs
configuracion_servidores = {}


# --- HELPER FOR LOGS ---
async def send_log(guild, embed):
    # 1. Buscamos el canal en la memoria (Línea 26)
    canal_id = configuracion_servidores.get(guild.id)

    if canal_id:
        canal = guild.get_channel(canal_id)
        if canal:
            try:
                await canal.send(embed=embed)
                return
            except Exception as e:
                print(f"❌ Error al enviar log: {e}")

    # 2. Si no hay configuración, buscamos el canal "logs"
    canal_auto = next(
        (c for c in guild.text_channels if "logs" in c.name.lower()), None)
    if canal_auto:
        try:
            await canal_auto.send(embed=embed)
        except Exception as e:
            print(f"❌ Error en canal automático: {e}")
    else:
        print(f"⚠️ No se encontró canal de logs en {guild.name}")



# --- 1. MODERATION COMMANDS (ENGLISH) ---


@bot.tree.command(name="ban", description="Permanently ban a user")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    # --- 1. ESTO ES LO NUEVO: Enviar el MD ---
    try:
        # 1. Definimos el nombre del servidor de forma segura
        servidor_nombre = interaction.guild.name if interaction.guild else "el servidor"
        
        # 2. Creamos el mensaje
        embed_aviso = discord.Embed(
            title="🚫 Notificación de Seguridad",
            description=f"Se te ha vetado de **{servidor_nombre}**.\n\n**Razón:** {reason}",
            color=0xff0000
        )
        # 3. Lo enviamos
        await user.send(embed=embed_aviso)
    except Exception:
        # Si tiene los MD bloqueados, el bot sigue adelante
        pass

    # --- 2. Tu código original de baneo (Línea 88 aprox) ---
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {user.mention} ha sido baneado. Razón: {reason}")
    # --- 2. Tu código original de baneo ---
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {user.mention} has been banned. Reason: {reason}")


@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member):
    await user.kick()
    await interaction.response.send_message(
        f"👢 {user.mention} has been kicked.")


@bot.tree.command(name="mute", description="Mute a user (Timeout)")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction,
               user: discord.Member,
               minutes: int,
               reason: str = "No reason"):
    duration = datetime.timedelta(minutes=minutes)
    await user.timeout(duration, reason=reason)
    await interaction.response.send_message(
        f"🔇 {user.mention} muted for {minutes}m. Reason: {reason}")


@bot.tree.command(name="unmute", description="Remove mute from a user")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, user: discord.Member):
    await user.timeout(None)
    await interaction.response.send_message(f"🔊 {user.mention} is now unmuted.")

@bot.tree.command(name="clear", description="Borra una cantidad específica de mensajes")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, cantidad: int):
    # Avisamos a Discord que vamos a tardar (evita el error 404)
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Purgamos los mensajes
        deleted = await interaction.channel.purge(limit=cantidad) # type: ignore
        # Respondemos con followup porque usamos defer
        await interaction.followup.send(f"✅ Se han borrado {len(deleted)} mensajes.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ No pude borrar los mensajes: {e}", ephemeral=True)

# --- 2. WARN SYSTEM ---


@bot.tree.command(name="warn", description="Warn a user (3 warns = Kick)")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction,
               user: discord.Member,
               reason: str = "No reason"):
    user_id = str(user.id)
    bot.warns[user_id] = bot.warns.get(user_id, 0) + 1
    total = bot.warns[user_id]
    await interaction.response.send_message(
        f"⚠️ {user.mention} warned ({total}/3). Reason: {reason}")
    if total >= 3:
        await user.kick(reason="3/3 Warns")
        bot.warns[user_id] = 0


@bot.tree.command(name="remove_warn", description="Remove 1 warn from a user")
@app_commands.checks.has_permissions(moderate_members=True)
async def remove_warn(interaction: discord.Interaction, user: discord.Member):
    user_id = str(user.id)
    if bot.warns.get(user_id, 0) > 0:
        bot.warns[user_id] -= 1
        await interaction.response.send_message(
            f"✅ Removed 1 warn from {user.name}. Total: {bot.warns[user_id]}")
    else:
        await interaction.response.send_message(f"❌ {user.name} has no warns.")


# --- 3. UTILITY & ROLES ---


@bot.tree.command(name="create_role",
                  description="Create a new role in the server")
@app_commands.checks.has_permissions(manage_roles=True)
async def create_role(interaction: discord.Interaction,
                      name: str,
                      color_hex: str = "ffffff"):
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    color = int(color_hex.replace("#", ""), 16)
    await interaction.guild.create_role(name=name,
                                        color=discord.Color(color))
    await interaction.response.send_message(
        f"🎨 Role `{name}` created successfully!")


@bot.tree.command(name="support", description="Get the support server link")
async def support(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🆘 Need help? Join here: https://discord.gg/XyPvtnWZY")


@bot.tree.command(name="set_logs", description="Set the log channel")
@app_commands.checks.has_permissions(administrator=True)
async def set_logs(interaction: discord.Interaction,
                   channel: discord.TextChannel):
    bot.log_channel_id = channel.id
    await interaction.response.send_message(f"✅ Logs set to {channel.mention}")


@bot.tree.command(name="estado", description="Mira el estado actual del pato")
async def estado(interaction: discord.Interaction):
    ping = round(bot.latency * 1000)
    servidores = len(bot.guilds)
    usuarios = sum((guild.member_count or 0) for guild in bot.guilds)

    embed = discord.Embed(title="🛰️ 𝐄𝐒𝐓𝐀𝐃𝐎 𝐃𝐄𝐋 𝐁𝐎𝐓", color=0x2ecc71)

    embed.add_field(name="🟢 𝐒𝐭𝐚𝐭𝐮𝐬", value="`Online`", inline=False)
    embed.add_field(name="💻 𝐒𝐞𝐫𝐯𝐢𝐝𝐨𝐫𝐞𝐬", value=f"`{servidores}`", inline=True)
    embed.add_field(name="👥 𝐔𝐬𝐮𝐚𝐫𝐢𝐨𝐬", value=f"`{usuarios}`", inline=True)
    embed.add_field(name="📶 𝐏𝐢𝐧𝐠", value=f"`{ping} ms`", inline=False)

    from datetime import datetime
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    embed.set_footer(text=f"Última actualización: {ahora} • Rubius_Gamer07")
    if bot.user and bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)

    # Enviamos el mensaje y guardamos la respuesta en una variable
    await interaction.response.send_message(embed=embed)
    mensaje = await interaction.original_response()

    # El bot añade las reacciones solo (puedes cambiar los emojis)
    await mensaje.add_reaction("✅")
    await mensaje.add_reaction("🇪🇸")
    await mensaje.add_reaction("❤️")


@bot.tree.command(name="servers", description="Muestra la lista actualizada de servidores")
async def servers(interaction: discord.Interaction):
    # Esto obliga al bot a pedirle a Discord la lista real de este segundo
    guilds_actuales = bot.guilds 
    
    nombres = [f"• {g.name} (ID: {g.id})" for g in guilds_actuales]
    lista_final = "\n".join(nombres)
    
    await interaction.response.send_message(
        f"Estoy en **{len(guilds_actuales)}** servidores:\n{lista_final}", 
        ephemeral=True
    )


@bot.tree.command(name="announce",
                  description="Envía un anuncio oficial a través del bot")
@app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction,
                   mensaje: str,
                   titulo: str = "📢 𝐀𝐍𝐔𝐍𝐂𝐈𝐎 𝐎𝐅𝐈𝐂𝐈𝐀𝐋"):
    embed = discord.Embed(
        title=titulo,
        description=mensaje,
        color=0xe67e22  # Naranja chill para que resalte
    )

    embed.set_footer(
        text=
        f"Anuncio enviado por {interaction.user.display_name} • Duck Security")
    if bot.user and bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)

    # El bot confirma que lo envió (solo lo ves tú) y luego lo manda al canal
    await interaction.response.send_message("✅ Anuncio enviado con éxito.",
                                            ephemeral=True)
    if interaction.channel and isinstance(interaction.channel, discord.abc.Messageable):
        await interaction.channel.send(embed=embed)

@bot.tree.command(name="set-log", description="Configura el canal de logs")
@app_commands.checks.has_permissions(administrator=True)
async def set_log(interaction: discord.Interaction,
                  canal: discord.TextChannel):
    # Esto usa la 'memoria' que creamos en la línea 26
    configuracion_servidores[interaction.guild_id] = canal.id
    await interaction.response.send_message(
        f"✅ Logs configurados en {canal.mention}")


@bot.tree.command(name="userinfo",
                  description="Mira los datos de un miembro del server")
async def userinfo(interaction: discord.Interaction,
                   miembro: discord.Member | None = None):
    miembro = miembro or interaction.user  # type: ignore  # Si no mencionas a nadie, eres tú
    if not miembro:
        await interaction.response.send_message("No se pudo obtener la información del usuario.", ephemeral=True)
        return

    embed = discord.Embed(title=f"👤 𝐈𝐍𝐅𝐎 𝐃𝐄 {miembro.display_name}",
                          color=0x3498db)
    embed.set_thumbnail(url=miembro.display_avatar.url)

    embed.add_field(name="🆔 ID", value=f"`{miembro.id}`", inline=True)
    embed.add_field(name="🗓️ Se unió a Discord",
                    value=miembro.created_at.strftime("%d/%m/%Y"),
                    inline=True)
    embed.add_field(name="🏠 Se unió al server",
                    value=miembro.joined_at.strftime("%d/%m/%Y") if miembro.joined_at else "Desconocido",
                    inline=True)
    embed.add_field(name="🎭 Roles",
                    value=f"{len(miembro.roles) - 1}",
                    inline=True)

    embed.set_footer(
        text=f"Solicitado por {interaction.user.name} • Duck Security")
    await interaction.response.send_message(embed=embed)


# 1. El evento para capturar el mensaje
@bot.event
async def on_message_delete(message):
    bot.snipes[message.channel.id] = (message.content, message.author,
                                      message.created_at)


# 2. El comando para mostrarlo
@bot.tree.command(name="snipe",
                  description="Muestra el último mensaje borrado")
async def snipe(interaction: discord.Interaction):
    if not interaction.channel:
        await interaction.response.send_message("❌ No se pudo obtener el canal.", ephemeral=True)
        return
    if interaction.channel.id in bot.snipes:
        contenido, autor, fecha = bot.snipes[interaction.channel.id]
        embed = discord.Embed(description=contenido,
                              color=0xf1c40f,
                              timestamp=fecha)
        embed.set_author(name=f"Mensaje de {autor.name}",
                         icon_url=autor.display_avatar.url)
        embed.set_footer(text="Pillado por Duck Security")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "❌ No hay nada que snipear aquí.", ephemeral=True)


@bot.tree.command(name="serverinfo",
                  description="Muestra toda la info del servidor")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("Este comando solo funciona en un servidor.", ephemeral=True)
        return

    embed = discord.Embed(title=f"🏰 𝐈𝐍𝐅𝐎 𝐃𝐄 {guild.name}", color=0x2ecc71)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

    embed.add_field(name="👑 Dueño",
                    value=f"{guild.owner.mention}" if guild.owner else "Desconocido",
                    inline=True)
    embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="📅 Creado el",
                    value=guild.created_at.strftime("%d/%m/%Y"),
                    inline=True)
    embed.add_field(name="👥 Miembros",
                    value=f"`{guild.member_count}`",
                    inline=True)
    embed.add_field(
        name="💬 Canales",
        value=
        f"`{len(guild.text_channels)}` Texto | `{len(guild.voice_channels)}` Voz",
        inline=False)

    embed.set_footer(text="Duck Security | Seguridad & Vibes")
    await interaction.response.send_message(embed=embed)
    
    
@bot.event
async def on_member_join(member):
    # --- CONFIGURACIÓN DE SOPORTE ---
    id_mi_soporte = 1466077655391666176# <--- ID sacada de tu contexto

    # 1. Si entran a tu server de soporte, el bot no los echa
    if member.guild.id == id_mi_soporte:
        print(f"Usuario {member.name} entró a soporte para apelar.")
        return 

    # 2. FILTRO ANTIBALAS (Blacklist Global)
    if member.id in blacklist_ids:
        try:
            await member.kick(reason="Blacklist Global - Apela en el server de soporte.")
            return # Esto corta el proceso para que no le de la bienvenida
        except Exception:
            print(f"No pude echar a {member.name}")

    # 3. Log de nuevo miembro (Esto solo si no fue expulsado)
    log_embed = discord.Embed(
        title="📥 NUEVO MIEMBRO",
        description=f"{member.mention} ha entrado al servidor.",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now()
    )
    log_embed.set_thumbnail(url=member.display_avatar.url)
    log_embed.add_field(name="Cuenta creada el:", value=member.created_at.strftime("%d/%m/%Y"))
    
    await send_log(member.guild, log_embed)

    # 4. Mensaje de bienvenida
    channel = discord.utils.get(member.guild.text_channels, name="👋┃bienvenidas")
    if not channel:
        channel = next((c for c in member.guild.text_channels if "bienvenida" in c.name.lower()), None)

    if channel:
        embed = discord.Embed(
            title="✨ ¡Un nuevo miembro ha llegado!",
            description=f"¡Qué onda {member.mention}! Bienvenido al equipo. Pásatelo genial y no olvides leer las reglas. 🦆",
            color=0xf1c40f
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Eres el miembro número {member.guild.member_count}")
        await channel.send(embed=embed)

@bot.tree.command(name="celebrar",
                  description="Lanza una ráfaga de confeti y celebración")
async def celebrar(interaction: discord.Interaction, motivo: str):
    embed = discord.Embed(
        title="🥳 ¡𝐂𝐄𝐋𝐄𝐁𝐑𝐀𝐂𝐈Ó𝐍!",
        description=
        f"**{interaction.user.name}** está celebrando:\n\n✨ `{motivo}` ✨",
        color=0xff00ff)
    embed.set_image(
        url=
        "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzR6NHJmZzR6NHJmZzR6NHJmZzR6NHJmZzR6NHJmZzR6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/l0MYt5jPR6QX5pnqM/giphy.gif"
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="top",
    description="Muestra el ranking de los 5 usuarios con más nivel")
async def top(interaction: discord.Interaction):
    # Si no hay nadie con XP todavía
    if not bot.levels:
        await interaction.response.send_message(
            "🦆 ¡El ranking está vacío! Empieza a escribir para ser el primero.",
            ephemeral=True)
        return

    # Ordenamos a los usuarios de mayor a menor nivel y XP
    ranking = sorted(bot.levels.items(),
                     key=lambda x: (x[1]['level'], x[1]['xp']),
                     reverse=True)

    embed = discord.Embed(
        title="🏆 𝐑𝐀𝐍𝐊𝐈𝐍𝐆 𝐃𝐄 𝐍𝐈𝐕𝐄𝐋𝐄𝐒",
        description="Aquí están los mejores patos del estanque:",
        color=0xffd700  # Color dorado
    )

    # Sacamos el top 5
    for i, (user_id, data) in enumerate(ranking[:5], 1):
        user = bot.get_user(int(user_id))
        nombre = user.name if user else f"Usuario {user_id}"
        embed.add_field(
            name=f"#{i} - {nombre}",
            value=f"✨ Nivel: **{data['level']}** | 🧪 XP: **{data['xp']}**",
            inline=False)

    embed.set_footer(text="¡Sigue chateando para subir!")
    await interaction.response.send_message(embed=embed)


@bot.event
async def on_member_remove(member):
    embed = discord.Embed(
        title="📤 MIEMBRO HA SALIDO",
        description=f"**{member.name}** ha abandonado el servidor.",
        color=discord.Color.red(),
        timestamp=datetime.datetime.now())
    await send_log(member.guild, embed)


@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return

    embed = discord.Embed(title="📝 MENSAJE EDITADO",
                          description=f"En el canal {before.channel.mention}",
                          color=discord.Color.blue(),
                          timestamp=datetime.datetime.now())
    embed.add_field(name="Antes:",
                    value=before.content or "Sin contenido",
                    inline=False)
    embed.add_field(name="Después:",
                    value=after.content or "Sin contenido",
                    inline=False)
    embed.set_author(name=before.author.name,
                     icon_url=before.author.display_avatar.url)
    await send_log(before.guild, embed)


@bot.event
async def on_guild_channel_create(channel):
    embed = discord.Embed(title="🆕 CANAL CREADO",
                          description=f"Nombre: {channel.name}",
                          color=0x2ecc71)

    await send_log(channel.guild, embed)


@bot.event
async def on_guild_channel_delete(channel):
    embed = discord.Embed(title="🗑️ CANAL ELIMINADO",
                          description=f"Nombre: {channel.name}",
                          color=0xe74c3c)
    await send_log(channel.guild, embed)


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        if before.channel is None:
            desc = f"📥 {member.mention} entró a **{after.channel.name}**"
            col = discord.Color.green()
        elif after.channel is None:
            desc = f"📤 {member.mention} salió de **{before.channel.name}**"
            col = discord.Color.red()
        else:
            desc = f"🔄 {member.mention} se movió de **{before.channel.name}** a **{after.channel.name}**"
            col = discord.Color.blue()

        embed = discord.Embed(title="🎙️ Cambio en Voz",
                              description=desc,
                              color=col,
                              timestamp=datetime.datetime.now())
        await send_log(member.guild, embed)


@bot.event
async def on_member_update(before, after):
    embed = discord.Embed(title=f"👤 Actualización de Miembro: {before.name}",
                          color=0xf1c40f,
                          timestamp=datetime.datetime.now())

    # Cambio de Apodo
    if before.nick != after.nick:
        embed.add_field(name="Apodo Anterior",
                        value=f"`{before.nick}`",
                        inline=True)
        embed.add_field(name="Apodo Nuevo",
                        value=f"`{after.nick}`",
                        inline=True)
        await send_log(before.guild, embed)

    # Cambio de Roles
    if before.roles != after.roles:
        agregados = [r.mention for r in after.roles if r not in before.roles]
        quitados = [r.mention for r in before.roles if r not in after.roles]
        if agregados:
            embed.add_field(name="✅ Roles añadidos",
                            value=", ".join(agregados))
        if quitados:
            embed.add_field(name="❌ Roles quitados", value=", ".join(quitados))
        await send_log(before.guild, embed)


@bot.event
async def on_member_ban(guild, user):
    embed = discord.Embed(
        title="🔨 USUARIO BANEADO",
        description=f"**{user.name}** ha sido expulsado permanentemente.",
        color=0x992d22,
        timestamp=datetime.datetime.now())
    embed.set_thumbnail(url=user.display_avatar.url)
    await send_log(guild, embed)


@bot.event
async def on_raw_reaction_add(payload):
    # Obtenemos el servidor y el usuario
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    user = await bot.fetch_user(payload.user_id)
    if user.bot:
        return

    embed = discord.Embed(
        title="😀 REACCIÓN AÑADIDA",
        description=
        f"**{user.name}** reaccionó con {payload.emoji} en un mensaje.",
        timestamp=datetime.datetime.now())

    # Usamos nuestra nueva función con color morado
    await send_log(guild, embed)


@bot.tree.command(name="avatar", description="𝐌𝐮𝐞𝐬𝐭𝐫𝐚 𝐞𝐥 𝐚𝐯𝐚𝐭𝐚𝐫 𝐝𝐞 𝐮𝐧 𝐮𝐬𝐮𝐚𝐫𝐢𝐨")
async def avatar(interaction: discord.Interaction,
                 usuario: discord.Member | None = None):
    # Si no eligen a nadie, el usuario es quien puso el comando
    usuario = usuario or interaction.user  # type: ignore
    if not usuario:
        await interaction.response.send_message("No se pudo obtener el usuario.", ephemeral=True)
        return

    # Creamos el diseño con tus letras bonitas
    embed = discord.Embed(
        title=f"📸 𝐀𝐕𝐀𝐓𝐀𝐑 𝐃𝐄 {usuario.display_name.upper()}",
        color=0xFFA500,  # Naranja pato
        timestamp=datetime.datetime.now())

    # Ponemos la imagen en grande
    embed.set_image(url=usuario.display_avatar.url)
    embed.set_footer(text=f"Solicitado por: {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)

# Variable para guardar el ID del último sorteo (para el reroll)
ultimo_sorteo_id = None

@bot.command()
@commands.has_permissions(administrator=True)
async def crearsorteo(ctx, tiempo: int, ganadores: int, *, premio: str):
    global ultimo_sorteo_id
    
    embed = discord.Embed(
        title="🎉 ¡SORTEO ACTIVO! 🎉",
        description=f"🎁 **Premio:** {premio}\n👤 **Ganadores:** {ganadores}\n⏳ **Duración:** {tiempo}s",
        color=0x00ff00 # Verde
    )
    embed.set_footer(text="Reacciona con 🎉 para participar")
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    ultimo_sorteo_id = msg.id # Guardamos el ID para el futuro reroll

    await asyncio.sleep(tiempo)

    # Proceso de finalización
    nuevo_msg = await ctx.channel.fetch_message(msg.id)
    usuarios = [u async for u in nuevo_msg.reactions[0].users() if not u.bot]

    if len(usuarios) < ganadores:
        await ctx.send(f"⚠️ No hay suficientes participantes para: **{premio}**.")
    else:
        afortunados = random.sample(usuarios, ganadores)
        menciones = ", ".join([u.mention for u in afortunados])
        await ctx.send(f"🎊 ¡Felicidades {menciones}! Ganaste: **{premio}**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def reroll(ctx):
    global ultimo_sorteo_id
    
    if ultimo_sorteo_id is None:
        return await ctx.send("❌ No hay ningún sorteo registrado recientemente para hacer reroll.")

    try:
        msg = await ctx.channel.fetch_message(ultimo_sorteo_id)
        usuarios = [u async for u in msg.reactions[0].users() if not u.bot]
        
        if not usuarios:
            return await ctx.send("❌ Nadie participó, no puedo elegir a un nuevo ganador.")

        ganador = random.choice(usuarios)
        await ctx.send(f"🎲 **Reroll:** ¡El nuevo ganador es {ganador.mention}! 🎉")
        
    except Exception as e:
        await ctx.send(f"❌ Error al buscar el sorteo: {e}")
@bot.command()
async def backrooms(ctx, *, usuario = None):
    # Si no hay usuario mencionado, el objetivo eres tú (ctx.author)
    objetivo = usuario or ctx.author
    
    embed = discord.Embed(
        title="⚠️ ERROR DE REALIDAD DETECTADO ⚠️",
        description=f"Parece que {objetivo.mention} ha hecho **noclip** fuera de los límites del servidor...",
        color=0xe2cc71 # El color amarillento de tu cap
    )
    embed.set_image(url="https://i.imgur.com/8nNnU0z.jpg") 
    embed.add_field(name="Ubicación Actual:", value="🟨 Nivel 0 - 'The Lobby'", inline=False)
    embed.set_footer(text="No te muevas. Algo te ha escuchado.")

    await ctx.send(embed=embed)
# --- SECCIÓN DE TERROR DUCK SECURITY ---

@bot.command()
async def invocar(ctx):
    suerte = random.randint(1, 100)
    if suerte <= 20:
        msg = await ctx.send("🕯️ **Iniciando ritual...**")
        await asyncio.sleep(2)
        await msg.edit(content="👣 *Se escuchan pasos detrás de ti...*")
        await asyncio.sleep(2)
        embed = discord.Embed(title="⚠️ ENTIDAD DETECTADA ⚠️", color=0x000000)
        embed.set_image(url="https://i.imgur.com/vHCHM1O.jpg")
        await ctx.send(embed=embed)
    else:
        await ctx.send("✨ El ritual ha fallado. Por ahora estás a salvo...")

@bot.command()
@commands.has_permissions(administrator=True)
async def blackout(ctx):
    aviso = await ctx.send("🚨 **ERROR DEL SISTEMA: SOBRECARGA ELÉCTRICA** 🚨")
    await asyncio.sleep(2)
    await aviso.edit(content="🌑 **Las luces se han apagado... no hagas ruido.**")
    for i in range(3):
        await asyncio.sleep(1)
        await ctx.send("...")
    await asyncio.sleep(5)
    await ctx.send("💡 **Energía restaurada.** ¿Sigues ahí?")

@bot.command()
async def susurro(ctx, *, usuario: discord.Member | None = None):
    objetivo = usuario or random.choice([m for m in ctx.guild.members if not m.bot])
    try:
        await objetivo.send(f"👤 **{objetivo.name}**... sé que puedes leerme. No te des la vuelta.")
        await ctx.send("🤫 Se ha enviado un susurro a las sombras...")
    except Exception:
        await ctx.send(f"🌑 {objetivo.mention} está protegido por el silencio...")

@bot.command()
async def glitch(ctx):
    msg = await ctx.send("S-i-s-t-e-m-a O-p-t-i-m-o...")
    await asyncio.sleep(1)
    await msg.edit(content="E-R-R-O-R -- N-O-C-L-I-P --")
    await asyncio.sleep(1)
    await msg.edit(content="01001000 01000101 01001100 01010000")
    embed = discord.Embed(title="⚠️ REALIDAD CORRUPTA", color=0xff0000)
    embed.set_image(url="https://i.imgur.com/vHCHM1O.jpg")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def paranoia(ctx):
    msg = await ctx.send("¿Quién está detrás de ti?")
    await asyncio.sleep(0.5)
    await msg.delete()
    await ctx.send("👀 *Has sentido una mirada en tu nuca...*")

@bot.command()
async def horrorhelp(ctx):
    embed = discord.Embed(title="📂 ARCHIVOS CLASIFICADOS", color=0x2f3136)
    embed.add_field(name="🟨 !backrooms", value="Nivel 0.", inline=False)
    embed.add_field(name="🕯️ !invocar", value="Ritual aleatorio.", inline=False)
    embed.add_field(name="🌑 !blackout", value="Apaga el servidor.", inline=False)
    embed.add_field(name="🤫 !susurro", value="Mensaje privado.", inline=False)
    embed.add_field(name="👾 !glitch", value="Error visual.", inline=False)
    embed.add_field(name="👀 !paranoia", value="Susto rápido.", inline=False)
    embed.set_thumbnail(url="https://i.imgur.com/8nNnU0z.jpg")
    await ctx.send(embed=embed)


@bot.tree.command(name="blacklist", description="Añade a alguien a la lista negra y lo echa de todos los servers")
@app_commands.describe(usuario_id="La ID numérica del usuario", razon="¿Por qué se va a la lista negra?")
async def blacklist(interaction: discord.Interaction, usuario_id: str, razon: str):
    if interaction.user.id != 1257319843875786843:
        return await interaction.response.send_message("❌ No tienes permisos para usar la seguridad global.", ephemeral=True)

    try:
        target_id = int(usuario_id)
        if target_id not in blacklist_ids:
            blacklist_ids.append(target_id)
        
        embed = discord.Embed(
            title="🚫 BLACKLIST GLOBAL APLICADA",
            description=f"El usuario con ID `{target_id}` ha sido vetado de la red Duck.",
            color=0xf04747
        )
        embed.add_field(name="Motivo:", value=razon)
        embed.set_footer(text="Seguridad Duck • Moderación Multi-Server")

        servidores_limpios = 0
        for guild in bot.guilds:
            member = guild.get_member(target_id)
            if member:
                try:
                    await member.send(embed=embed)
                except Exception:
                    pass
                
                try:
                    await member.kick(reason=f"Blacklist Global: {razon}")
                    servidores_limpios += 1
                except discord.Forbidden:
                    print(f"⚠️ Sin permisos para echar en {guild.name}")
                except Exception as e:
                    print(f"⚠️ Error en {guild.name}: {e}")

        msg = f"✅ ID `{target_id}` añadida."
        if servidores_limpios > 0:
            msg += f" Expulsado de **{servidores_limpios}** servidores."
        
        await interaction.response.send_message(content=msg, embed=embed)

    except ValueError:
        await interaction.response.send_message("❌ ID inválida. Usa solo números.", ephemeral=True)
@bot.tree.command(name="unblacklist", description="Elimina a un usuario de la lista negra global")
@app_commands.describe(usuario_id="La ID numérica que quieres perdonar")
async def unblacklist(interaction: discord.Interaction, usuario_id: str):
    # Solo tú tienes la llave maestra
    if interaction.user.id != 1257319843875786843:
        return await interaction.response.send_message("❌ No tienes permisos, jefe.", ephemeral=True)

    try:
        target_id = int(usuario_id)
        if target_id in blacklist_ids:
            blacklist_ids.remove(target_id)
            
            embed = discord.Embed(
                title="✅ ACCESO RESTABLECIDO",
                description=f"El usuario con ID `{target_id}` ha sido eliminado de la lista negra.",
                color=0x43b581 # Verde de éxito
            )
            embed.set_footer(text="Seguridad Duck • Perdón concedido")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"⚠️ La ID `{target_id}` no estaba en la lista.", ephemeral=True)
            
    except ValueError:
        await interaction.response.send_message("❌ Pon una ID válida (solo números).", ephemeral=True)
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "El pato está vivo!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive() # Esto crea una mini web para que el bot no se duerma
@bot.tree.command(name="stats", description="Muestra las estadísticas globales del Pato")
async def stats(interaction: discord.Interaction):
    # Calculamos los datos en tiempo real
    total_servidores = len(bot.guilds)
    total_usuarios = sum(guild.member_count or 0 for guild in bot.guilds)
    total_blacklist = len(blacklist_ids)

    embed = discord.Embed(
        title="📊 ESTADÍSTICAS DE DUCK SECURITY",
        description="Aquí tienes el estado actual de mi red de protección global. 🦆🛡️",
        color=0xf1c40f, # Color amarillo pato
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(name="🌐 Servidores Protegidos", value=f"`{total_servidores}`", inline=True)
    embed.add_field(name="👥 Usuarios Vigilados", value=f"`{total_usuarios}`", inline=True)
    embed.add_field(name="🚫 Blacklist Global", value=f"`{total_blacklist}` usuarios", inline=False)
    
    if bot.user:
        embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"Solicitado por: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)
# ==========================================
#         EVENTOS DE INTERACCIÓN 🦆
# ==========================================

# 1. CUANDO ALGUIEN ESCRIBE (MENCIÓN)
@bot.event
async def on_message(message):
    # Protección: Ignorar mensajes de otros bots o fuera de servidores
    if message.author.bot or not message.guild:
        return

    # Si mencionan al bot (con tus emojis animados)
    if bot.user and bot.user.mentioned_in(message) and not message.mention_everyone:
        pepo_booba = "<a:PepoBooba:1479839236730388540>"
        pepo_danza = "<a:PepoDans:1479839081243476018>"
        pepo_dinero = "<a:PepoMoney:1479839549223075983>"
        
        embed = discord.Embed(
            title=f"{pepo_danza} ¡Hola! Soy Duck Security",
            description=(
                f"{pepo_booba} Hola {message.author.mention}, ¡estoy aquí para ayudar!\n\n"
                f"{pepo_dinero} Si quieres ver mis estadísticas actuales, prueba el comando `/stats`."
            ),
            color=0xf1c40f
        )
        if bot.user:
            embed.set_thumbnail(url=bot.user.display_avatar.url)
        await message.channel.send(embed=embed)

    # IMPORTANTE: Esto permite que los comandos / sigan funcionando
    await bot.process_commands(message)

# 2. CUANDO EL BOT SE UNE A UN NUEVO SERVIDOR
@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            pepo_booba = "<a:PepoBooba:1479839236730388540>"
            pepo_danza = "<a:PepoDans:1479839081243476018>"
            
            embed = discord.Embed(
                title=f"{pepo_booba} ¡Cuaaac! He llegado a la ciudad",
                description=(
                    f"{pepo_danza} ¡Hola! Gracias por dejarme cuidar de **{guild.name}**.\n\n"
                    f"🛡️ Estoy aquí para ayudar a que este servidor sea un lugar seguro y divertido."
                ),
                color=0xf1c40f
            )
            embed.add_field(
                name="🚀 ¿Por dónde empiezo?", 
                value="Prueba el comando `/stats` para ver mi red de protección activa.", 
                inline=False
            )
            if bot.user:
                embed.set_thumbnail(url=bot.user.display_avatar.url)
            
            embed.set_footer(text="Duck Security • Tu servidor está en buenas manos.")
            
            await channel.send(embed=embed)
            break

# --- SUSTITUYE EL FINAL (desde el thread de flask) POR ESTO ---

def run_flask():
    # El puerto DEBE ser 7860 para Hugging Face
    app.run(host='0.0.0.0', port=7860)

if __name__ == "__main__":
    # 1. Arrancamos Flask para que Hugging Face vea que estamos "Running"
    import threading
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # 2. Inicializamos el bot
    bot = MyBot()
    bot.warns = {}
    bot.snipes = {}
    bot.levels = {}

# 3. LEEMOS Y LIMPIAMOS EL TOKEN
# Usamos el nombre DISCORD_TOKEN para evitar bloqueos de red
raw_token = os.environ.get('DISCORD_TOKEN', '')
clean_token = raw_token.strip()

if not clean_token:
    print("❌ ERROR: El Secreto 'DISCORD_TOKEN' no existe o está vacío en Settings.")
else:
    try:
            import aiohttp
            import asyncio
            print("🚀 Aplicando parche de red con DNS externo y lanzando...")
            
            async def start_bot():
                # Forzamos el uso de IPv4 y desactivamos la caché de DNS interna
                connector = aiohttp.TCPConnector(use_dns_cache=False, family=0)
                async with aiohttp.ClientSession(connector=connector) as session:
                    bot.http.connector = connector
                    await bot.start(clean_token)

            asyncio.run(start_bot())
    except Exception as e:
        print(f"❌ FALLO DEFINITIVO: {e}")
