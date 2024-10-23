import requests
import json
from bs4 import BeautifulSoup
import datetime

def extract_patch_titles(data):
    # This function should be implemented to parse the JSON data
    # and extract the URLs for each patch's detailed information.
    # Return a list of URLs.

    # For example, if the JSON data looks like this:
    # {
    #     "parse": {
    #         "text": {
    #             "*": "<div>
    #                     ....
    #                     <h2>
    #                         <span class="mw-headline" id="List_of_seasons">List of Patches</span>
    #                     </h2>
    #                     <ul>
    #                         <li>
    #                             <a href="/wiki/Patch_(League_of_Legends)/Season_Thirteen" title="Patch (League of Legends)/Season Thirteen">Season Thirteen</a>
    #                         </li>
    #                         <li>
    #                             <a href="/wiki/Patch_(League_of_Legends)/Season_Twelve" title="Patch (League of Legends)/Season Twelve">Season Twelve</a>
    #                         </li>
    #                         ...
    #                     </ul>
    #                     ...
    #                 </div>"
    #         }
    #     }
    # }
    # Then the function should return a list like this:
    # [
    #     'Patch (League of Legends)/Season Thirteen',
    #     'Patch (League of Legends)/Season Twelve',
    #     ...
    # ]

    text = data['parse']['text']['*']
    soup = BeautifulSoup(text, 'html.parser')
    patch_list = soup.find('span', {'id': 'List_of_seasons'}).find_next('ul').find_all('a')

    patch_urls = []
    for patch in patch_list:
        patch_urls.append(patch['title'])

    return patch_urls
    
def fetch_season_details(title):
    url = 'https://leagueoflegends.fandom.com/api.php?action=parse&page=' + title + '&format=json'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Get the patch tables. Usually includes season and pre-season tables
    text = data['parse']['text']['*']
    soup = BeautifulSoup(text, 'html.parser')
    tables = soup.find_all('table', {'class': 'wikitable'})

    # Example output:
    # <table align="left" border="1" cellspacing="0" class="wikitable" style="text-align:center; border-collapse:collapse; border:1px solid #444; width:100%; color:white;">
    #  <tbody>
    #   <tr>
    #    <th>
    #     December 8
    #     <br/>
    #     2021
    #     <br/>
    #     <a class="external autonumber" href="https://na.leagueoflegends.com/en-us/news/game-updates/patch-11-24-notes/" rel="nofollow noreferrer noopener" target="_blank">
    #      [22]
    #     </a>
    #    </th>
    #    <td>
    #     <a href="/wiki/V11.24" title="V11.24">
    #      V11.24
    #     </a>
    #    </td>
    #    <td>
    #     ...
    #    </td>
    #   </tr>
    #  </tbody>
    # </table>

    # Parse the tables. Extract the patches and dates
    # For each 'tr' tag, the first 'th' tag contains the date and the second 'td' tag contains the patch

    patchesWithDates = []

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            # If there is a 'th' tag, it contains the date. Then, the first 'td' tag contains the patch
            # If there is no 'th' tag, then the first 'td' tag contains the date and the second 'td' tag contains the patch
            date = row.find('th')
            patch = None

            if date is None:
                date = row.find_all('td')[0]
                patch = row.find_all('td')[1]
            else:
                patch = row.find('td')

            if patch is None or date is None:
                continue

            patch = patch.find('a').get_text()
            date = date.get_text()

            # Remove the starting V from patch if it exists
            if patch[0] == 'V':
                patch = patch[1:]

            # November 22022[1]\n
            # Remove [ and everything after it
            # Remove ( and everything after it
            date = date.split('[')[0]
            date = date.split('(')[0]

            # If there is a - like June 17–202012 remove the - and the numbers before it (1 digit or 2 digits), but keep the month
            # Get the index of the -
            dashIndex = date.find('–')
            if dashIndex != -1:
                # Check if there is 1 digit or 2 digits before the -
                if date[dashIndex - 2].isdigit():
                    date = date[:dashIndex - 2] + date[dashIndex + 1:]
                else:
                    date = date[:dashIndex - 1] + date[dashIndex + 1:]

            # November 22022
            # Separate the date and year by putting a comma before the last 4 characters
            date = date[:-4] + ', ' + date[-4:]

            # November 2, 2022
            # Convert the date to a timestamp
            date = datetime.datetime.strptime(date, '%B %d, %Y').timestamp()

            # 1699430400.0
            # Remove the .0
            date = int(date)

            patchesWithDates.append({
                'name': patch,
                'start': date
            })

    return patchesWithDates

def get_region_shifts():
    return {
        'OC1': -46800,
        'JP1': -43200,
        'KR': -39600,
        'RU': -28800,
        'EUN1': -21600,
        'TR1': -18000,
        'EUW1': -10800,
        'BR1': -3600,
        'LA2': 0,
        'LA1': 7200,
        'NA1': 10800,
        'PH': 43200,
        'ID1': 43200,
        'VN': 46800,
        'SG': 50400,
        'TH': 54000,
        'TW': 57600
    }

def main():
    response = requests.get('https://leagueoflegends.fandom.com/api.php?action=parse&page=Patch_(League_of_Legends)&format=json')
    response.raise_for_status()
    seasons = response.json()

    patch_titles = extract_patch_titles(seasons)

    # Do not include the alpha and closed beta patches
    patch_titles = patch_titles[:-2]

    patches = []
    for title in patch_titles:
        patch_data = fetch_season_details(title)
        
        for patch in patch_data:
            patches.append(patch)

    # Sort the patches by start date
    patches.sort(key=lambda x: x['start'])

    shifts = get_region_shifts()

    patchesWithShifts = {
        'patches': patches,
        'shifts': shifts
    }

    # Save the data to a JSON file
    with open('patches.json', 'w') as f:
        json.dump(patchesWithShifts, f)

if __name__ == '__main__':
    main()
