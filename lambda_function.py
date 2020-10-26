import json
from bs4 import BeautifulSoup
import aiohttp
import html
import asyncio

URL = "https://liquipedia.net/rocketleague/api.php"

PARAMS_NA = {
    'action': "parse",
    'pageid': 89823,
    'prop': 'text',
    'section': 1,
    'format': "json"
}

PARAMS_EU = {
    'action': "parse",
    'pageid': 89816,
    'prop': 'text',
    'section': 1,
    'format': "json"
}


async def get_table(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            print('getting table for ' + str(params))
            data = await response.json()
            html_unescaped = html.unescape(data['parse']['text']['*'])
            parsed_html = BeautifulSoup(html_unescaped, features="html.parser")
            results = filter_results(parsed_html)
            team_entries = gather_team_entries(results)
            return team_entries


def filter_results(parsed_html):
    results = filter(lambda x: str(x.get('data-toggle-area-content')) == '6', parsed_html.find_all('tr'))
    results = filter(lambda x: x.find('span', attrs={'class': 'team-template-team-standard'}) is not None,
                     results)
    return results


def gather_team_entries(results):
    team_entries = {}
    for team_entry in results:
        team_name = team_entry.find('span', attrs={'class': 'team-template-text'}).text
        tds = team_entry.findAll('td')
        team_entries[team_name] = tds[3].text
    return team_entries


async def get_region_tables():
    return await asyncio.gather(asyncio.create_task(get_table(URL, PARAMS_NA)),
                                asyncio.create_task(get_table(URL, PARAMS_EU)))


tables = {}


def get_region_tables_sync():
    if 'NA' not in tables or 'EU' not in tables:
        (na_table, eu_table) = asyncio.get_event_loop().run_until_complete(get_region_tables())
        tables['NA'] = na_table
        tables['EU'] = eu_table


def lambda_handler(event, context):
    get_region_tables_sync()
    na_table = json.dumps(tables['NA'])
    eu_table = json.dumps(tables['EU'])
    return {
        'statusCode': 200,
        'body': {
            'NA': na_table,
            'EU': eu_table
        }
    }


def main():
    print(lambda_handler('', ''))


if __name__ == "__main__":
    main()
