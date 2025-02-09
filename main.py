import requests
from bs4 import BeautifulSoup
import asyncio
import nest_asyncio
from telegram import Bot
from random import choice
import os
import json
import re

# Apply fix for nested event loops
nest_asyncio.apply()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
LATEST_PROJECT_FILE = "latest_project.json"

def load_latest_project():
    """Load the latest project title from a file (to persist across runs)."""
    if os.path.exists(LATEST_PROJECT_FILE):
        with open(LATEST_PROJECT_FILE, "r") as file:
            return json.load(file).get("latest_project", None)
    return None

def save_latest_project(title):
    """Save the latest project title to a file."""
    with open(LATEST_PROJECT_FILE, "w") as file:
        json.dump({"latest_project": title}, file)

async def send_telegram_message(message):
    """Send a message to Telegram."""
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    print("Message sent successfully!")
    print("_____________________________________________________")

async def send_project(title, project_url, tarikh_alnashr, almeezaneya, muddat_altanfeeth, moaadal_altoatheef, description):
    """Send project details to Telegram."""
    full_message = f"**{title}**\nURL: {project_url}\nتاريخ النشر: {tarikh_alnashr}\nالميزانية: {almeezaneya}\nمدة التنفيذ: {muddat_altanfeeth}\nمعدل التوظيف: {moaadal_altoatheef}\n\n{description}"
    try:
        print(full_message)
        await send_telegram_message(full_message)
    except Exception as e:
        error_message = f"Failed to send message due to error: {e}"
        print(error_message)
        try:
            await send_telegram_message(error_message)
        except Exception as inner_e:
            print(f"Failed to send error notification: {inner_e}")

def get_soup(url, user_agents):
    """Fetch page content and return a BeautifulSoup object."""
    for _ in range(3):
        try:
            headers = {"User-Agent": choice(user_agents)}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            asyncio.sleep(5)
    return None

async def extract_project_info():
    """Scrape project details from Mostaql."""
    latest_project_title = load_latest_project()

    url = 'https://mostaql.com/projects?category=development,marketing,support&budget_max=10000&sort=latest'
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    ]
    
    soup = get_soup(url, user_agents)
    if not soup:
        print("Failed to retrieve the page content.")
        return

    projects = soup.find_all('tr', class_='project-row')
    if not projects:
        print("No projects found.")
        return

    title_element = projects[0].find('h2', class_='mrg--bt-reset').find('a')
    current_latest_project = title_element.text.strip()

    if latest_project_title == current_latest_project:
        print("No new projects found. Stopping scraping.")
        return

    for project in projects:
        title_element = project.find('h2', class_='mrg--bt-reset').find('a')
        title = title_element.text.strip()
        project_url = title_element['href']

        if latest_project_title == title:
            print("_____________________________________________________")
            print("Stopping scraping.")
            save_latest_project(current_latest_project)
            return

        project_soup = get_soup(project_url, user_agents)
        if project_soup:
            description_container = project_soup.find('div', class_='text-wrapper-div carda__content')
            description = '\n'.join([p.text.strip() for p in description_container.find_all('p')]) if description_container else "Description not found"

            project_details = project_soup.find('div', id='project-meta-panel')
            tarikh_alnashr = project_details.find('td', string='تاريخ النشر').find_next_sibling('td').get_text(strip=True) if project_details else "Not found"
            almeezaneya = project_details.find('td', string='الميزانية').find_next_sibling('td').get_text(strip=True) if project_details else "Not found"
            muddat_altanfeeth = project_details.find('td', string='مدة التنفيذ').find_next_sibling('td').get_text(strip=True) if project_details else "Not found"
            moaadal_altoatheef = project_details.find('span', string='معدل التوظيف').find_parent('tr').find_all('td')[1].get_text(strip=True) if project_details else "0%"

            try:
                employment_rate = float(re.sub(r'\D', '', moaadal_altoatheef))  # Extract numbers safely
                if employment_rate >= 80:
                    await send_project(title, project_url, tarikh_alnashr, almeezaneya, muddat_altanfeeth, moaadal_altoatheef, description)
            except (ValueError, AttributeError):
                pass

    save_latest_project(current_latest_project)

async def main():
    """Main function to run the scraper once (for Railway cron job)."""
    await extract_project_info()

if __name__ == "__main__":
    asyncio.run(main())
