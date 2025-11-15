import aiohttp
import asyncio

class FMP:
    def __init__(self):
        self.api_key = '1kordurUCvK73cauxe8xuoggIPE6EIPs'

    async def fetch(self, session: aiohttp.ClientSession, url: str, params: dict[str]):
        async with session.get(url=url, params=params) as response:
            if response.status != 200:
                response.raise_for_status()
            return await response.json()

    async def make_requests(self, company_tickers: list[str], url: str, extra_params: dict[str]):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for ticker in company_tickers:
                # Attach company ticker to param
                extra_params['apikey'] = self.api_key
                extra_params['symbol'] = ticker

                task = asyncio.create_task(self.fetch(session, url, extra_params))
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            return results

    async def get_quotes(self, company_tickers: list[str]):
        base_url = 'https://financialmodelingprep.com/stable/quote'
        res = await self.make_requests(company_tickers, base_url)

        return (
        {
            ticker: {
                'symbol': res[i]['symbol'],
                'dayLow': res[i]['dayLow'],
                'dayHigh': res[i]['dayHigh'],
            }
            for i, ticker in enumerate(company_tickers)}
        )

    async def get_incomes(self, company_tickers: list[str]):
        base_url = 'https://financialmodelingprep.com/stable/income-statement'
        res = await self.make_requests(company_tickers, base_url)

        return (
        {
            ticker: {
                'symbol': res[i]['symbol'],
                'revenue': res[i]['revenue'],
                'dayHigh': res[i]['dayHigh'],
            }
            for i, ticker in enumerate(company_tickers)}
        )

async def main():
    fmp = FMP()
    test_tickers = ['AAPL', 'AMZN', 'GOOG']
    print(fmp.get_quotes(test_tickers))
    print(fmp.get_incomes(test_tickers))

if __name__ == '__main__':
    asyncio.run(main())