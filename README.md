# RoXeT Emoji Extractor

ربات خصوصی تلگرام: ایموجی پریمیوم (Custom Emoji) را می‌گیرد و شناسه عددی، نماد و **فایل اصلی** (TGS / WEBM / WEBP) را برمی‌گرداند. فقط با توکن ربات کار می‌کند؛ بدون شماره تلفن و بدون session حساب شخصی. فقط مالک ربات اجازه استفاده دارد.

دکمه‌ها رنگی (سبز / آبی / قرمز) هستند. این ویژگی نیاز به نسخه‌ی جدید تلگرام (بعد از ۹ فوریه ۲۰۲۶) دارد؛ در نسخه‌های قدیمی دکمه‌ها بدون رنگ دیده می‌شوند.

## نصب سریع (Ubuntu / Debian)

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/USERNAME/REPOSITORY.git roxet_emoji_extractor
cd roxet_emoji_extractor
chmod +x install.sh
./install.sh
```

اسکریپت پکیج‌ها و venv را نصب می‌کند، توکن و آیدی عددی مالک را می‌پرسد و در `.env` ذخیره می‌کند، و سرویس `roxet-emoji` را با systemd فعال می‌کند. نصب بدون سرویس: `./install.sh --no-service`.

## نیازمندی‌ها
- Python 3.10 یا بالاتر
- توکن ربات از @BotFather
- آیدی عددی تلگرام خودت

## نصب دستی
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env
.venv/bin/python emojibot.py
```

## مدیریت سرویس
```bash
sudo systemctl status roxet-emoji
sudo journalctl -u roxet-emoji -f
sudo systemctl restart roxet-emoji
```

## استفاده
`/start` را بزن و ایموجی پریمیوم را مستقیم بفرست (تا ۱۰ ایموجی در یک پیام). شناسه عددی را هم می‌توانی تنها بفرستی.

## امنیت
فایل `.env` شامل توکن ربات است؛ هرگز در گیت‌هاب نگذار (در `.gitignore` است). توکن در لاگ‌ها چاپ نمی‌شود.
