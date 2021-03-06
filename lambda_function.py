import json
from bs4 import BeautifulSoup
import aiohttp
import html
import asyncio
from enum import Enum

URL = "https://liquipedia.net/rocketleague/api.php"

PARAMS_NA = {
    'action': "parse",
    'pageid': 89821,
    'prop': 'text',
    'section': 1,
    'format': "json"
}

PARAMS_EU = {
    'action': "parse",
    'pageid': 89815,
    'prop': 'text',
    'section': 1,
    'format': "json"
}

PARAMS_OCE = {
    'action': "parse",
    'pageid': 91700,
    'prop': 'text',
    'section': 1,
    'format': "json"
}

PARAMS_SAM = {
    'action': "parse",
    'pageid': 91528,
    'prop': 'text',
    'section': 1,
    'format': "json"
}


class Region(Enum):
    EU = 'EU'
    NA = 'NA'
    SAM = 'SAM'
    OCE = 'OCE'


async def get_table(url, params, region):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            print('getting table for ' + str(params))
            data = await response.json()
            html_unescaped = html.unescape(data['parse']['text']['*'])
            parsed_html = BeautifulSoup(html_unescaped, features="html.parser")
            results = filter_results(parsed_html, region)
            team_entries = gather_team_entries(results)
            return team_entries


async def write_html_to_file(html_unescaped):
    parsed_html_encoded = BeautifulSoup(html_unescaped, features="html.parser")
    parsed_html_encoded.encode('utf8')
    f = open('eu_html.html', 'w', encoding='utf8')
    f.write(str(parsed_html_encoded.prettify(formatter='html5')))
    f.close()


def filter_results(parsed_html, region):
    data_toggle_area_content = '12'
    if region in [Region.EU]:
        data_toggle_area_content = '8'
    if region in [Region.OCE]:
        data_toggle_area_content = '7'
    elif region in [Region.SAM]:
        data_toggle_area_content = '4'
    results = filter(lambda x: str(x.get('data-toggle-area-content')) == data_toggle_area_content,
                     parsed_html.find_all('tr'))
    results = filter(lambda x: x.find('span', attrs={'class': 'team-template-team-standard'}) is not None, results)
    return results


def gather_team_entries(results):
    team_entries = {}
    for team_entry in results:
        team_name = team_entry.find('span', attrs={'class': 'team-template-text'}).text
        tds = team_entry.findAll('td')
        team_entries[team_name] = tds[3].text
    return team_entries


async def get_region_tables():
    return await asyncio.gather(asyncio.create_task(get_table(URL, PARAMS_NA, Region.NA)),
                                asyncio.create_task(get_table(URL, PARAMS_EU, Region.EU)),
                                asyncio.create_task(get_table(URL, PARAMS_OCE, Region.OCE)),
                                asyncio.create_task(get_table(URL, PARAMS_SAM, Region.SAM)))


tables = {}


def get_region_tables_sync():
    if 'NA' not in tables or 'EU' not in tables:
        (na_table, eu_table, oce_table, sa_table) = asyncio.get_event_loop().run_until_complete(get_region_tables())
        tables['NA'] = na_table
        tables['EU'] = eu_table
        tables['OCE'] = oce_table
        tables['SAM'] = sa_table


def lambda_handler(event, context):
    get_region_tables_sync()
    return {
        'statusCode': 200,
        'body': json.dumps(tables)
    }


def main():
    print(lambda_handler('', ''))


if __name__ == "__main__":
    main()
