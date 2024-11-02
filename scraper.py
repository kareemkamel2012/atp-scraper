from collections import defaultdict
import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = '/usr/bin/google-chrome'

service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)


APP_SERVER_URL = os.getenv('APP_SERVER_URL', 'http://localhost:4200')

def rank_to_int(rank_string):
    if rank_string[-1].isalpha():
        return int(rank_string[:-1])
    else:
        return int(rank_string)
import re
from datetime import datetime

#Claude-3 Sonnet!
def parse_dates(date_range_str):
    # Regular expression patterns to match the two date range formats
    same_month_pattern = r"(\d{1,2})\s*-\s*(\d{1,2})\s*(\w+),\s*(\d{4})"
    different_month_pattern = r"(\d{1,2})\s*(\w+)\s*-\s*(\d{1,2})\s*(\w+),\s*(\d{4})"
    
    # Match the pattern against the input string
    same_month_match = re.match(same_month_pattern, date_range_str)
    different_month_match = re.match(different_month_pattern, date_range_str)
    
    if same_month_match:
        # Extract the start date, end date, month, and year from the match groups
        start_day = int(same_month_match.group(1))
        end_day = int(same_month_match.group(2))
        month_name = same_month_match.group(3)
        year = int(same_month_match.group(4))
        
        # Convert the month name to a number (1-12)
        month = datetime.strptime(month_name, "%B").month
        
        # Create datetime objects for the start and end dates
        start_date = datetime(year, month, start_day)
        end_date = datetime(year, month, end_day)
        
    elif different_month_match:
        # Extract the start date, start month, end date, end month, and year from the match groups
        start_day = int(different_month_match.group(1))
        start_month_name = different_month_match.group(2)
        end_day = int(different_month_match.group(3))
        end_month_name = different_month_match.group(4)
        year = int(different_month_match.group(5))
        
        # Convert the month names to numbers (1-12)
        start_month = datetime.strptime(start_month_name, "%B").month
        end_month = datetime.strptime(end_month_name, "%B").month
        
        # Create datetime objects for the start and end dates
        start_date = datetime(year, start_month, start_day)
        end_date = datetime(year, end_month, end_day)
        
    else:
        return None, None
    
    # Format the dates as ISO strings (YYYY-MM-DD)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    return start_date_str, end_date_str

def find_players():
    PLAYERS_URL = "https://www.atptour.com/en/rankings/singles?RankRange=0-5000&Region=all&DateWeek=Current%20Week"
    page = requests.get(PLAYERS_URL)

    soup = BeautifulSoup(page.content, "html.parser")

    player_rows = soup.find_all("tr", class_="lower-row")
    players = []
    for row in player_rows:
        [id, rank, player_name] = [None] * 3
        link = row.find("a")
        id = extract_player_id(link["href"])
        name_container = row.find("li", class_="name center")
        if name_container:
            player_name = name_container.find("span").text.strip()
        rank = rank_to_int(row.find("td", class_="rank").text.strip())

        if player_name and rank:
            players.append({'id': id, 'rank': rank, 'name': player_name})
    
    return players
    
def scrape_tournament_page(url):
    driver.get(url)
    driver.implicitly_wait(5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    surface = soup.find('span', string='Surface')
    if surface is not None:
        surface = surface.find_next_sibling('span').string
        if surface is not None:
            surface = surface.strip()
        else:
            surface = "Hard"
    else:
        surface = "Hard"

    return surface

def find_placements(link):

    def to_name(link):
        hyphenated_name = link.split('/')[3]
        return hyphenated_name.replace('-', ' ').title()
    
    driver.get(link)
    driver.implicitly_wait(5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    placements = defaultdict(list)

    columns = soup.find_all("div", class_="draw")
    semifinals = columns[-2]
    finals = columns[-1]
    semifinal_cells = semifinals.find_all("div", class_="stats-item")
    for cell in semifinal_cells:
        if not cell.find("div", class_="winner"):
            player_link = cell.find("a")
            if player_link:
                placements['semifinalists'].append(to_name(player_link['href']))
    final_cells = finals.find_all("div", class_="stats-item")
    for cell in final_cells:
        player_link = cell.find("a")
        if player_link:
            if cell.find("div", class_="winner"):
                placements['winners'].append(to_name(player_link['href']))
            else:
                placements['finalists'].append(to_name(player_link['href']))

    return placements

def find_tournaments():
    TOURNAMENTS_URL = "https://www.atptour.com/en/tournaments"
    driver.get(TOURNAMENTS_URL)
    driver.implicitly_wait(5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    events_containers = soup.find_all("ul", class_="events")
    events = sum([event_container.find_all("li") for event_container in events_containers], [])
    tournaments = []
    for event in events:
        tournament_id, tournament_name, points, location, start_end = [None] * 5
        placements = {}
        banner = event.find("img", class_="events_banner")
        if banner:
            image = banner["src"] if "src" in banner.attrs else None
            if image == '/assets/atpwt/images/tournament/badges/categorystamps_250.png':
                points = 250
            elif image == '/assets/atpwt/images/tournament/badges/categorystamps_500.png':
                points = 500
            elif image == '/assets/atpwt/images/tournament/badges/categorystamps_1000.png':
                points = 1000
            elif image == '/assets/atpwt/images/tournament/badges/categorystamps_finals.svg':
                points = 1500
            elif image == '/assets/atpwt/images/tournament/badges/categorystamps_grandslam.png':
                points = 2000
        if not points or points < 1000:
            continue
        tournament_name = event.find("span", class_="name").text.strip()
        date = event.find("span", class_="Date")
        if date:
            start_end = parse_dates(date.text.strip())
        location = event.find("span", class_="venue").text.strip()
        if location:
            location = location.rstrip(' |')

        tournament_overview_link = event.find("a", class_="tournament__page-link")
        if tournament_overview_link:
            tournament_id = tournament_overview_link["href"].split('/')[-3]
        results_button = event.find("a", class_="results")
        if results_button:
            parts = results_button["href"].rsplit("/")
            link = f'https://www.atptour.com{"/".join(parts[:-1] + ["draws"])}'
        else:
            link = None
        if link:
            if not (tournament_name and start_end and points and points >= 1000 and location):
                continue
            placements = find_placements(link)
        surface = 'hard'
        overview_link = event.find("a", class_="tournament__page-link")
        if overview_link:
            overview_link = f'https://www.atptour.com{overview_link["href"]}'
            surface = scrape_tournament_page(overview_link)
        
        if tournament_id and tournament_name and start_end and location and points and points >= 1000 and surface:
            tournament_info = {}
            tournament_info['id'] = tournament_id
            tournament_info['name'] = tournament_name
            tournament_info['startDate'] = start_end[0]
            tournament_info['endDate'] = start_end[1]
            tournament_info['points'] = points
            tournament_info['location'] = location
            tournament_info['placements'] = placements
            tournament_info['surface'] = surface
            tournaments.append(tournament_info)
            print(f'added tournament: {tournament_info}')
        
    return tournaments

def extract_player_id(url):
    return url.split('/')[-2]

def get_atp_data():
    try:
        return {
            'players': find_players(),
            'tournaments': find_tournaments()
        }
    except Exception as e:
        print(e)
        raise(e)
    finally:
        driver.quit()