# bot_main.py

import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, ContextTypes)

from db_utils import check_daily_limit
from analytics import analyze_stock

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

STOCK_LIST = {
    # List 100+ saham IDX (hapus .JK), contoh:
    "BBCA", "BBRI", "BMRI", "TLKM", "ASII",
    # tambahkan sesuai kebutuhan
}

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Halo {user.first_name}!\n"
        f"/analisa <kode> — Technical + Broker\n"
        f"/broker <kode> — Hanya broker summary\n"
    )

async def analisa_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = "premium" if user_id == ADMIN_ID else "free"
    if not check_daily_limit(user_id, status):
        await update.message.reply_text("⚠️ Limit harian tercapai.")
        return

    if not ctx.args:
        await update.message.reply_text("Gunakan: /analisa <kode_saham>\nContoh: /analisa BBCA")
        return

    kode = ctx.args[0].upper()
    if kode not in STOCK_LIST:
        await update.message.reply_text("⚠️ Kode saham tidak didukung.")
        return

    await update.message.reply_text(f"⏳ Menganalisa teknikal + broker summary untuk *{kode}.JK* …", parse_mode="Markdown")

    try:
        summary, decision = analyze_stock(kode)
    except Exception as e:
        logging.error("Analisa error: %s", e)
        await update.message.reply_text(f"❌ Gagal analisa: {e}")
        return

    text = (
        f"*{summary['symbol']}* | Harga: `{summary['price']:.0f}`\n"
        f"• RSI: `{summary['rsi']:.2f}` | Volume Ratio: `{summary['vol_ratio']:.2f}x`\n\n"
        "*Broker Summary (Net Lot ≥ threshold):*\n"
        + ("\n".join(summary["broker_summary"]) if summary["broker_summary"] else "_– tidak ada broker dominan_")
        + f"\n\n💡 *Decision:* {decision}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def broker_only_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Hanya menampilkan broker summary (tanpa teknikal)"""
    user_id = update.effective_user.id
    status = "premium" if user_id == ADMIN_ID else "free"
    if not check_daily_limit(user_id, status):
        await update.message.reply_text("⚠️ Limit harian tercapai.")
        return

    if not ctx.args:
        await update.message.reply_text("Gunakan: /broker <kode_saham>")
        return

    kode = ctx.args[0].upper()
    try:
        brk_list = fetch_broker_summary(kode)
    except Exception as e:
        logging.error("broker fetch fail: %s", e)
        await update.message.reply_text(f"❌ Gagal fetch broker summary: {e}")
        return

    if not brk_list:
        await update.message.reply_text("⚠️ Tidak ditemukan data broker.")
        return

    text = f"*{kode}.JK* — Broker Top {len(brk_list)}\n"
    for b in brk_list:
        text += f"• {b['broker']}: ±{b['net_lot']:,} lot (Beli {b['buy_lot']:,} / Jual {b['sell_lot']:,})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("🚨 TELEGRAM_BOT_TOKEN tidak ditemukan di .env")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("analisa", analisa_command))
    application.add_handler(CommandHandler("broker", broker_only_command))
    application.add_handler(MessageHandler(filters.COMMAND, start))

    logging.info("Bot Telegram siap dijalankan.")
    application.run_polling()

if __name__ == "__main__":
    main()
