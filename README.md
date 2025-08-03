git clone <repo-url>
cd my_idx_bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium  # Penting untuk jalankan Playwright
