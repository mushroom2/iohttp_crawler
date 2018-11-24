from bs4 import BeautifulSoup
import requests
import re
import asyncio
import aiohttp
import json
from  os import path
targeturl = 'https://www.flickr.com/photos/saver_ag'
path_to_save = '/home/mushroom/lasoft/iohttpbs4/res'

def get_pag_list(url):
    limit = 1
    r = requests.get(url)
    if r.status_code == 200:
        s = BeautifulSoup(r.content, 'html.parser')
        lim = s.find('div', {'class': 'view pagination-view requiredToShowOnServer photostream'})
        for elem in lim.find_all('a'):
            rawlim = re.sub(r'\D+', '', elem['href'])
            limit = int(rawlim) if rawlim and rawlim.isdigit() and int(rawlim) > limit else limit
        return ['{u}/page{i}'.format(u=url, i=itm) for itm in range(1, limit + 1)]


def get_photos(tjd):
    res = []
    for i in tjd:
        if i and isinstance(i, dict) and i.get('sizes'):
            res.append('https:' + i['sizes']['o']['displayUrl'])
    return res


async def fetch(session, url, met):
    async with session.get(url) as resp:
        if met == 'page':
            return await resp.text()
        elif met == 'photo':
            return await resp.read()


async def save_photo(url, sess, pa):
    photoname = url.split('/')[-1]
    p = path.join(pa, photoname)
    with open(p, 'wb') as f:
        resp = await fetch(sess, url, 'photo')
        f.write(resp)


async def get_page(url):
    async with aiohttp.ClientSession() as sess:
        response = await fetch(sess, url, 'page')
        soup = BeautifulSoup(response)
        targetscript = soup.find_all('script', {'class': 'modelExport'})
        if len(targetscript) and re.search(r'modelExport: (.*),', targetscript[0].text):
            # target json
            tj = json.loads(re.search(r'modelExport: (.*),', targetscript[0].text).group(1))
            photos = get_photos(tj['main']['photostream-models'][0]['photoPageList']['_data'])
            for p in photos:
                await save_photo(p, sess, path_to_save)


async def start():
    tasks = [get_page(i) for i in get_pag_list(targeturl)]
    await asyncio.wait(tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
    loop.close()
