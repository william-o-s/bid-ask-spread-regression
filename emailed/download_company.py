'''
Retrieves the required regression data for each stock ticker.
'''
import numpy as np
import pandas as pd
import yfinance as yf
from collections import Counter
from curl_cffi import requests
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

class Company:
    '''Helper class to store representation of company financials'''

    dependent_variable_name = 'Bid-Ask Spread'

    ################################################################################################
    ################################################################################################
    ################################# EDIT FROM THIS LINE ONWARDS! #################################
    ################################################################################################
    ################################################################################################

    def __init__(self, ticker: str, info: dict[str]):
        self.ticker = ticker

        # Natural log of TTM revenues
        ttm_revenues = info['totalRevenue']
        ln_revenues = self.get_ln_revenues(ttm_revenues)

        # DERN: dummy var for positive earnings, 0 if negative and 1 if positive
        profit_margins = info['profitMargins']
        dern = self.get_dern(profit_margins)

        # Firm value (proxy by YahooFinance Enterprise Value)
        enterprise_val = info['enterpriseValue']

        # Cash-to-Firm Value
        cash = info['totalCash']
        cash_to_ev = self.get_cash_to_ev(cash, enterprise_val)

        # $ Monthly Trading Volume-to-Firm Value
        # $ Monthly Trading Volume = 200-day average price * 3-month average volume
        three_month_volume = info['averageDailyVolume3Month']
        two_hundred_day_avg = info['twoHundredDayAverage']
        vol_to_ev = self.get_vol_to_ev(three_month_volume, two_hundred_day_avg, enterprise_val)

        # Bid-ask spread as a % of price
        bid = info['bid']
        ask = info['ask']
        price = info['currentPrice']
        spread = self.get_spread(bid, ask, price)

        ### Additional experiments

        # Debt-to-Firm Value
        debt = info['totalDebt']
        debt_to_ev = self.get_debt_to_ev(debt, enterprise_val)

        # Revenue growth
        revenue_growth = info['revenueGrowth']

        # Return on assets
        roa = info['returnOnAssets']

        # EPS growth estimate
        # eps_current_year = info['epsCurrentYear']
        # eps_next_year = info['epsForward']
        # eps_growth = self.get_eps_growth(eps_current_year, eps_next_year)

        # Variables that don't work - remove from damodaran's
        # 5-year monthly beta
        # beta_5ym = info['beta']

        # Payout ratio
        # payout_ratio = info['payoutRatio']
        # assert payout_ratio >= 0, f"{self.ticker} has negative payout ratio: {payout_ratio}"

        # Return on equity
        # roe = info['returnOnEquity']

        '''
        Use the following structure to add variables to the model:
            ...
            'Variable Name': Variable Value,
            ...
        '''

        self.data = {
            'Log Revenues': ln_revenues,
            'DERN': dern,
            'Cash-to-EV': cash_to_ev,
            'Volume-to-EV': vol_to_ev,

            'Debt-to-EV': debt_to_ev,
            'Revenue Growth': revenue_growth,
            'Return on Assets': roa,

            # Note: this funky looking code is just to maintain consistency;
            # Notice that dependent_variable_name = 'Bid-Ask Spread' above
            Company.dependent_variable_name: spread,
        }

    def get_ln_revenues(self, revenues: int):
        assert revenues > 0, f"{self.ticker} has negative or zero revenues: {revenues}"
        return np.log(revenues)

    def get_dern(self, profit_margins: float) -> bool:
        return (int)(profit_margins >= 0)

    def get_cash_to_ev(self, cash: int, ev: int) -> float:
        assert cash >= 0, f"{self.ticker} has negative cash: {cash}"
        assert ev != 0, f"{self.ticker} has zero EV (division by zero): {ev}"
        return cash / ev

    def get_vol_to_ev(self, vol_3month: int, price_3month: float, ev: int) -> float:
        assert vol_3month >= 0, f"{self.ticker} has negative volume: {vol_3month}"
        assert price_3month >= 0, f"{self.ticker} has negative average 3-month price: {price_3month}"
        assert ev != 0, f"{self.ticker} has zero EV (division by zero): {ev}"
        return (vol_3month * price_3month) / (3 * ev)   # Entire value divided by 3 to get monthly

    def get_debt_to_ev(self, debt: int, ev: int) -> float:
        assert debt >= 0, f"{self.ticker} has negative debt: {debt}"
        assert ev != 0, f"{self.ticker} has zero EV (division by zero): {ev}"
        return debt / ev

    def get_eps_growth(self, eps_current_year: float, eps_forward_est: float) -> float:
        eps_change = eps_forward_est - eps_current_year
        if eps_change == 0.0:
            return 0                                # No change in EPS
        if eps_current_year == 0:
            return np.sign(eps_change) * 1          # Current EPS is 0, change is non-zero, return 1 or -1 (100% or -100%)
        return eps_change / abs(eps_current_year)   # Current EPS is non-zero, return % change

    def get_spread(self, bid: int, ask: int, price: int) -> int:
        assert price > 0, f"{self.ticker} has negative or zero price (division by zero): {price}"
        assert bid >= 0, f"{self.ticker} has negative bid: {bid}"
        assert ask > 0, f"{self.ticker} has negative or zero ask: {ask}"
        assert ask > bid, f"{self.ticker} has negative or zero spread: {ask - bid}"
        return (ask - bid) / price

    ################################################################################################
    ################################################################################################
    ################################# DO NOT EDIT BELOW THIS LINE! #################################
    ################################################################################################
    ################################################################################################

    def get_df(self) -> pd.DataFrame | None:
        try:
            df = pd.DataFrame(list(self.data.values()), index=list(self.data.keys()), columns=[self.ticker]).T
        except AssertionError as e:
            return None
        return df

class YahooFinance:
    def __init__(self):
        self.session = CachedLimiterSession(
            limiter=Limiter(RequestRate(2, Duration.SECOND * 5)),  # Max 2 API calls every 5 sec
            bucket_class=MemoryQueueBucket,
            backend=SQLiteCache('yf.cache'),
        )
        self.session = requests.Session(impersonate='chrome')

    def download_companies(self, tickers: list[str]) -> dict[str, Company]:
        results = {}
        errors = []
        for ticker in tickers:
            try:
                data = yf.Ticker(ticker, session=self.session)
                # data = yf.Ticker(ticker)
                company = Company(ticker, data.info)
                results[ticker] = company
            except Exception as e:
                print('Error occurred while downloading data for company:', ticker)
                e_str = str(e)
                if str(e).startswith(ticker):
                    e_str = e_str.split(':')[0]
                    e_str = e_str[len(ticker):].strip()
                    errors.append(str(e)[len(ticker):].strip())
                    print(e)
                else:
                    print('No data exists for', e)
                print()

                errors.append(e_str)
                continue

        # Log which errors occur
        print('Frequency of errors when downloading:')
        for error, freq in Counter(errors).items():
            print(f"{error}: {freq}")

        return results

def main():
    test = YahooFinance()

    companies = [
        'AAPL',
        'BRK-B',
        'TSLA',
    ]
    data = test.download_companies(companies)

    for ticker, company in data.items():
        print(company.get_df())
        print('-' * 66, end='\n\n')

if __name__ == '__main__':
    main()
