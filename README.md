📌 Mostaql Scraper Bot
A web scraping bot that monitors Mostaql for new projects in development, marketing, and support categories, then sends notifications to a Telegram bot.

🚀 Features
Scrapes new projects from Mostaql.
Extracts project details like title, budget, duration, and employment rate.
Sends Telegram messages only for high-employment-rate projects (≥80%).
Uses BeautifulSoup and Requests for web scraping.
Implements error handling and automatic retries.
🛠️ Installation
1️⃣ Clone the Repository
sh
Copy
Edit
git clone https://github.com/your-username/mostaql-scraper.git
cd mostaql-scraper
2️⃣ Install Dependencies
sh
Copy
Edit
pip install -r requirements.txt
3️⃣ Set Up Environment Variables
Create a .env file in the project root and add:

env
Copy
Edit
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
Or, set them in the terminal:

sh
Copy
Edit
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
4️⃣ Run the Bot
sh
Copy
Edit
python main.py
📡 Deployment
🚀 Deploy on Railway
Login to Railway
sh
Copy
Edit
railway login
Initialize Railway Project
sh
Copy
Edit
railway init
Set Environment Variables
sh
Copy
Edit
railway variables set TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_chat_id
Deploy
sh
Copy
Edit
railway up
📜 Usage
The bot checks for new projects every 2 minutes.
Only sends messages for projects with employment rate ≥80%.
If an error occurs, it notifies the Telegram bot.
🛑 Troubleshooting
If you get Failed to send message errors, ensure:
Your Telegram bot token and chat ID are correct.
The bot is added to the group and has permission to send messages.
If no projects are found, the website structure may have changed—inspect it manually.
📄 License
This project is licensed under the MIT License.

👨‍💻 Author
👤 Mohab Wafaie
📧 Email: mohab.wafaie@gmail.com
🔗 GitHub: MohabWafaie

