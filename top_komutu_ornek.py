
@router.message(Command("top"))
async def top_cmd(message: Message):
    data = load_data().get("users", {})
    sirali = sorted(
        data.items(),
        key=lambda item: item[1].get("bakiye", 0) + item[1].get("banka", 0),
        reverse=True
    )[:10]

    if not sirali:
        await message.answer("🏆 Henüz hiç kullanıcı yok.")
        return

    msg = "🏆 <b>EN ZENGİN 10 Kişi (✨ Toplam • Bakiye • Banka✨ )</b>\n\n"
    for i, (uid, user_data) in enumerate(sirali, 1):
        toplam = user_data.get("bakiye", 0) + user_data.get("banka", 0)
        try:
            user = await message.bot.get_chat(uid)
            if user.username:
                isim = f"@{user.username}"
            else:
                isim = f"{user.first_name} {user.last_name or ''}"
        except:
            isim = f"ID:{uid}"

        sembol = "🏆" if i == 1 else "✨"
        msg += f"{sembol} {i}. Kullanıcı: {isim} — {toplam:,}₺ 💸\n"

    await message.answer(msg, parse_mode="HTML")
