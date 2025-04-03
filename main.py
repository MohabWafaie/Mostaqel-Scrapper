import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
from random import choice
import time
import os

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PERSISTENCE_FILE = 'latest_project.txt'
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
]

async def send_telegram_message(message, is_error=False):
    """Send message to Telegram with error handling"""
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
        print(f"{'Error ' if is_error else ''}Message sent successfully")
        print("___________________________________________________________________")
        return True
    except Exception as e:
        print(f"Critical error sending {'error ' if is_error else ''}message: {str(e)}")
        return False

def load_latest_projects():
    """Load the latest two project titles from the persistence file."""
    try:
        with open(PERSISTENCE_FILE, 'r') as f:
            return f.read().strip().split('\n')[:2]  # Load up to two titles
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading latest projects: {str(e)}")
        raise  # Propagate error to caller

def save_latest_projects(titles):
    """Save the latest two project titles to the persistence file."""
    try:
        with open(PERSISTENCE_FILE, 'w') as f:
            f.write('\n'.join(titles[:2]))  # Save up to two titles
    except Exception as e:
        print(f"Error saving latest projects: {str(e)}")
        raise  # Propagate error to caller

def get_soup(url):
    for _ in range(3):
        try:
            headers = {"User-Agent": choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Request error: {str(e)}")
            time.sleep(5)
    return None

async def process_project(project):
    """Process individual project with comprehensive error handling"""
    try:
        title_element = project.find('h2', class_='mrg--bt-reset').find('a')
        title = title_element.text.strip()
        project_url = title_element['href']
    except AttributeError as e:
        await send_telegram_message(f"🔍 Project structure error: {str(e)}", is_error=True)
        return None

    project_soup = get_soup(project_url)
    if not project_soup:
        await send_telegram_message(f"🚫 Failed to fetch project: {title}", is_error=True)
        return None

    try:
        description_container = project_soup.find('div', class_='text-wrapper-div carda__content')
        description = '\n'.join([p.text.strip() for p in description_container.find_all('p')]) if description_container else "No description"
    except Exception as e:
        description = "Description unavailable"
        await send_telegram_message(f"📄 Description error: {str(e)}", is_error=True)

    details = {}
    try:
        project_details = project_soup.find('div', id='project-meta-panel')
        if project_details:
            details = {
                'tarikh_alnashr': project_details.find('td', string='تاريخ النشر').find_next_sibling('td').text.strip(),
                'almeezaneya': project_details.find('td', string='الميزانية').find_next_sibling('td').text.strip(),
                'muddat_altanfeeth': project_details.find('td', string='مدة التنفيذ').find_next_sibling('td').text.strip(),
                'moaadal_altoatheef': project_details.find('span', string='معدل التوظيف').find_parent('tr').find_all('td')[1].text.strip()
            }
        else:
            details = {key: "Not found" for key in ['tarikh_alnashr', 'almeezaneya', 'muddat_altanfeeth', 'moaadal_altoatheef']}
    except Exception as e:
        await send_telegram_message(f"📊 Detail extraction error: {str(e)}", is_error=True)
        details = {key: "Error" for key in ['tarikh_alnashr', 'almeezaneya', 'muddat_altanfeeth', 'moaadal_altoatheef']}

    try:
        employment_rate = float(details['moaadal_altoatheef'].rstrip('%'))
        if employment_rate >= 70:
            message = (
                f"<b>{title}</b>\n"
                f"URL: {project_url}\n"
                f"تاريخ النشر: {details['tarikh_alnashr']}\n"
                f"الميزانية: {details['almeezaneya']}\n"
                f"مدة التنفيذ: {details['muddat_altanfeeth']}\n"
                f"معدل التوظيف: {details['moaadal_altoatheef']}\n\n"
                f"{description}"
            )
            print(message)
            success = await send_telegram_message(message)
            if not success:
                await send_telegram_message(f"❌ Failed to send project: {title}", is_error=True)
                print(f"Failed to send project: {title}")
            await asyncio.sleep(1)  # Non-blocking sleep
    except (ValueError, AttributeError):
        if details['moaadal_altoatheef'] != "لم يحسب بعد":
            print("Could not parse employment rate", details['moaadal_altoatheef'])
        pass
    except Exception as e:
        await send_telegram_message(f"⚠️ Unexpected project error: {str(e)}", is_error=True)

async def check_projects():
    """Main project checking logic with original order processing."""
    try:
        print("\nStarting project check...")
        url = 'https://mostaql.com/projects?category=development,marketing,support&budget_max=10000&sort=latest'
        
        soup = get_soup(url)
        if not soup:
            await send_telegram_message("⚠️ Failed to fetch project list", is_error=True)
            return

        projects = soup.find_all('tr', class_='project-row')
        if not projects:
            print("No projects found")
            return

        try:
            latest_projects = load_latest_projects()
        except Exception as e:
            await send_telegram_message(f"📁 Persistence load error: {str(e)}", is_error=True)
            latest_projects = []

        new_projects = []

        # Process in website order (newest first)
        for project in projects:
            try:
                title_element = project.find('h2', class_='mrg--bt-reset').find('a')
                title = title_element.text.strip()
                
                # Stop when reaching one of the last processed projects
                if latest_projects and title in latest_projects:
                    print("Reached last known project, stopping collection")
                    break
                
                new_projects.append(project)
            except Exception as e:
                await send_telegram_message(f"🔍 Project listing error: {str(e)}", is_error=True)
                continue

        if not new_projects:
            print("No new projects found")
            return

        # Process new projects in website order (newest first)
        for project in new_projects:
            await process_project(project)

        # Update persistence with the newest two projects
        try:
            latest_titles = [
                project.find('h2', class_='mrg--bt-reset').find('a').text.strip()
                for project in new_projects[:2]
            ]
            save_latest_projects(latest_titles)
            print(f"Saved new latest projects: {latest_titles}")
        except Exception as e:
            await send_telegram_message(f"💾 Failed to save latest projects: {str(e)}", is_error=True)

    except Exception as e:
        await send_telegram_message(f"🔥 Critical error in check_projects: {str(e)}", is_error=True)

async def main():
    """Main async entry point"""
    try:
        await check_projects()
    except Exception as e:
        await send_telegram_message(f"🚨 Fatal application error: {str(e)}", is_error=True)

if __name__ == "__main__":
    # Initialize persistence file
    if not os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, 'w') as f:
                pass
        except Exception as e:
            asyncio.run(send_telegram_message(f"📁 Failed to create persistence file: {str(e)}", is_error=True))

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Service stopped")
    except Exception as e:
        asyncio.run(send_telegram_message(f"⚡ Unexpected global error: {str(e)}", is_error=True))