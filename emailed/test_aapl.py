'''
Sample run with Apple.
'''

import json
import yfinance as yf

# Bid: .info['bid']
# Ask: .info['ask']

# TTM revenues: .info['totalRevenue']
# Profit margin: .info['profitMargins']
# Cash: .info['totalCash']
# Average trading volume (3 months): .info['averageDailyVolume3Month']
# 200-day moving average: .info['twoHundredDayAverage']
# Firm value (Enterprise value): .info['enterpriseValue']

# Revenue growth: .info['revenueGrowth']
# Earnings growth: .info['earningsGrowth']

# Payout ratio: .info['payoutRatio']
# 5Y beta: .info['beta']
# Debt: .info['totalDebt']

ticker = yf.Ticker('AAPL')

#convert info() output from dictionary to dataframe
print(json.dumps(ticker.info, indent=4))
print(ticker.info['currentPrice'])
