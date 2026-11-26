#!/usr/bin/env python3
"""RoXeT Emoji Extractor - private custom emoji ID/file helper (Bot API only)."""
import html
import io
import zipfile
import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# httpx logs full request URLs at INFO level, which contain the bot token.
for _noisy in ("httpx", "httpcore", "telegram"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
LOG = logging.getLogger("roxet-emoji")

MAX_IDS = 10
MAX_INT64 = 2**63 - 1
HTML = ParseMode.HTML

# Colored ("glass") inline buttons: primary = blue, success = green, danger = red.
BLUE, GREEN, RED = "primary", "success", "danger"

WELCOME = (
    "<b>✨ RoXeT Emoji Extractor</b>\n━━━━━━━━━━━━━━━━━━\n"
    "🎞 استخراج شناسه و فایل ایموجی سفارشی تلگرام\n\n"
    "ایموجی Premium را مستقیم در همین چت ارسال کن.\n"
    "<i>فایل در صورت دسترسی از تلگرام دریافت می‌شود.</i>"
)
TEXTS = {
    "extract": ("<b>🎞 استخراج ایموجی</b>\n\nایموجی Premium را به‌صورت مستقیم بفرست "
                "(تا ۱۰ ایموجی در یک پیام). می‌توانی خود شناسه عددی را هم بفرستی. "
                "اسکرین‌شات یا عکس ارسال نکن."),
    "help": ("<b>📘 راهنمای استفاده</b>\n\n۱) ایموجی سفارشی/پریمیوم را مستقیم ارسال کن.\n"
             "۲) منتظر دریافت شناسه و فایل بمان.\n\n"
             "⚠️ اگر تلگرام فایل ایموجی را در دسترس نگذارد، استخراج ممکن نیست."),
    "about": ("<b>RoXeT Emoji Extractor</b>\nابزار خصوصی برای بررسی شناسه و دریافت فایل ایموجی سفارشی.\n"
              "🔐 فقط مالک ربات مجاز است."),
}


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ استخراج ایموجی", callback_data="extract", style=GREEN),
         InlineKeyboardButton("📘 راهنما", callback_data="help", style=BLUE)],
        [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about", style=BLUE)],
    ])


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ منوی اصلی", callback_data="home", style=RED)]])


async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """True if the sender is an owner; otherwise politely refuse."""
    user = update.effective_user
    if user and user.id in context.application.bot_data["cfg"].owner_ids:
        return True
    if update.callback_query:
        await update.callback_query.answer("⛔ این ربات خصوصی است.", show_alert=True)
    else:
        chat, msg = update.effective_chat, update.effective_message
        if msg and chat and chat.type == "private":
            await msg.reply_text("⛔ این ربات خصوصی است.")
    return False


def file_ext(sticker) -> str:
    if sticker.is_animated:
        return ".tgs"
    if sticker.is_video:
        return ".webm"
    return ".webp"


def extract_ids(msg) -> list:
    """Custom emoji IDs from entities, or from a message that is only numeric IDs."""
    ids = []
    entities = msg.entities if msg.text else msg.caption_entities
    for ent in entities or ():
        if ent.type == MessageEntity.CUSTOM_EMOJI and ent.custom_emoji_id:
            cid = int(ent.custom_emoji_id)
            if cid not in ids:
                ids.append(cid)
    if not ids:
        text = (msg.text or msg.caption or "").strip()
        if text and re.fullmatch(r"[\d\s,،]+", text):
            for token in re.findall(r"\d{5,19}", text):
                cid = int(token)
                if cid <= MAX_INT64 and cid not in ids:
                    ids.append(cid)
    return ids


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await guard(update, context):
        await update.effective_message.reply_text(WELCOME, parse_mode=HTML, reply_markup=main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q or not await guard(update, context):
        return
    await q.answer()
    if q.data == "home":
        text, kb = WELCOME, main_menu()
    elif q.data in TEXTS:
        text, kb = TEXTS[q.data], back_menu()
    else:
        return
    try:
        await q.edit_message_text(text, parse_mode=HTML, reply_markup=kb)
    except BadRequest:
        pass  # "message is not modified"


async def emoji_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update, context):
        return
    msg = update.effective_message
    if not msg:
        return
    ids = extract_ids(msg)
    if not ids:
        await msg.reply_text("ایموجی سفارشی شناسایی نشد. ایموجی Premium را مستقیم در پیام بفرست.")
        return
    truncated = len(ids) > MAX_IDS
    ids = ids[:MAX_IDS]
    note = f"\n⚠️ فقط {MAX_IDS} ایموجی اول پردازش می‌شود." if truncated else ""
    status = await msg.reply_text(f"🔎 {len(ids)} ایموجی شناسایی شد\n⏳ در حال دریافت فایل...{note}")

    try:
        stickers = await context.bot.get_custom_emoji_stickers([str(i) for i in ids])
    except RetryAfter as exc:
        await status.edit_text(f"⏳ تلگرام محدودیت موقت گذاشته. {int(exc.retry_after)} ثانیه بعد دوباره امتحان کن.")
        return
    except Exception:
        LOG.exception("get_custom_emoji_stickers failed")
        await status.edit_text("❌ دریافت اطلاعات از تلگرام ناموفق بود.")
        return

    by_id = {s.custom_emoji_id: s for s in stickers if s.custom_emoji_id}
    sent, failed = 0, []
    for cid in ids:
        sticker = by_id.get(str(cid))
        if not sticker:
            failed.append(cid)
            continue
        try:
            tg_file = await sticker.get_file()
            data = bytes(await tg_file.download_as_bytearray())
            if not data:
                raise ValueError("empty download")
            name = f"emoji_{cid}{file_ext(sticker)}"
            alt = sticker.emoji or ""
            caption = (f"🆔 <code>{cid}</code>" + (f"  {html.escape(alt)}" if alt else "") +
                       f"\n📄 {name}{'.bin' if sticker.is_animated else ''} · {len(data) / 1024:.1f} KB" + ("\n⚠️ پسوند .bin را از آخر نام فایل حذف کن تا .tgs شود." if sticker.is_animated else ""))
            await msg.reply_document(document=data, filename=name + ('.bin' if sticker.is_animated else ''), caption=caption, parse_mode=HTML,
                                     read_timeout=60, write_timeout=60, connect_timeout=30,
                                     disable_content_type_detection=True)
            sent += 1
        except RetryAfter as exc:
            LOG.warning("RetryAfter %ss while sending %s", exc.retry_after, cid)
            failed.append(cid)
        except Exception:
            LOG.exception("Download/send failed for %s", cid)
            failed.append(cid)

    result = f"✅ {sent} فایل ارسال شد."
    if failed:
        result += "\n❌ ناموفق / بدون فایل در تلگرام:\n" + "\n".join(f"<code>{i}</code>" for i in failed)
    try:
        await status.edit_text(result, parse_mode=HTML)
    except BadRequest:
        pass


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    LOG.error("Unhandled error", exc_info=context.error)


def main() -> None:
    cfg = load_config()
    app = Application.builder().token(cfg.bot_token).connect_timeout(30).read_timeout(60).write_timeout(60).pool_timeout(30).build()
    app.bot_data["cfg"] = cfg
    app.add_handler(CommandHandler(["start", "help"], start_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, emoji_handler))
    app.add_error_handler(on_error)
    LOG.info("Bot running. Send a custom emoji to the bot in Telegram.")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
