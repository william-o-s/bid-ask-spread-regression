import aiohttp
import asyncio


async def fetch(url):
    async with aiohttp.ClientSession() as session:
        params = {
            'symbol': 'AAPL',
            'apikey': '1kordurUCvK73cauxe8xuoggIPE6EIPs',
            'limit': 1,
            'period': 'FY'
        }
        async with session.get(url=url, params=params) as response:
            if response.status != 200:
                response.raise_for_status()
            return await response.json()


res = asyncio.run(fetch('https://financialmodelingprep.com/stable/income-statement'))
print(res)