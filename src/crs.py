#! /usr/bin/python3

from yahoo_fin import stock_info as si
from datetime import datetime, timedelta
import numpy as np
#import matplotlib.pyplot as plot

# Configuration values
SYMBOLS = {'XLE', 'XLK', 'XOP', 'XLY', 'XLV', 'XLU', 'XLRE', 'XLP', 'XLI', 'XLF', 'XLC', 'XLB', 'SMH', 'IWM', 'DOW', 'QQQ', 'ARKK'}
BASE = 'SPY'
SMA_LENGTH = 20
UPTREND_SMA_LENGTH = 100
START_DATE = datetime.today() - timedelta(days=365)

def tickers():
    return SYMBOLS
    #return si.tickers_sp500()

# compare ticker/base for a ratio
def comparative_relative_strength(ticker_prices, base_prices):
    return [round((x/y), 6) for x,y in zip(ticker_prices, base_prices, strict=True)]
    
# rolling simple moving average over a sliding window
def calculate_sma(prices, length):
    # TODO throw if len(prices) < length
    return[(sum(prices[i:length+i])/length) for i in range(len(prices)-length+1)]

# same as crs itself so just call using sma points instead of closing price points
def calculate_crs_sma(closing_sma_data_set, base_sma_data_set):
    return comparative_relative_strength(closing_sma_data_set, base_sma_data_set)

# define uptrend by +dx/dy on the UPTREND_SMA_LENGTH
# or simply beta from a simple linear regression model
def is_uptrend(closing_prices):
    beta(range(len(closing_prices)), closing_prices)

def least_squares_fit(x_data, y_data):
    # TODO allow for 3 param to find the least squares regression of the last X points
    # TODO throw if len(x_data) != len(y_data)
    line = np.polyfit(x_data, y_data, 1)
    return line

if __name__ == '__main__':
    print(f'''
            CLI tool for finding the comparative relative strength of a stock symbol against a base symbol.
            Configuration options include:
                symbols - list of stock symbols to compare to the base. (default: {SYMBOLS})
                base - base symbol to compare symbols to for relative strength. (default: SPY)
                sma length - shorter term SMA used to calculate the SMA of the base, symbol, and the CRS SMA (data points are (SMA of symbol)/(SMA of base)). (default: 20)
                uptrend sma length - longer term SMA used to decide if the stock's closing price is in an uptrend by finding the least squares regression of the SMA of the length set here. (default: 100)
                start date - date from where data collection will begin. (default: 365)
                
            Output: Ordered list of symbols returned from `tickers()` function where the symbol is in an uptrend based on the UPTREND_SMA_LENGTH value and the crs sma is increasing based on the SMA_LENGTH value. Uptrend/increasing is determined by the least squares regression line having a positive beta.
          ''')
    closing_prices = {}
    crs = {}
    crs_sma = {}
    print(f'Pulling {BASE} data from {START_DATE.date()} until {datetime.today().date()} to use as denominator in CRS.')
    base_closing_prices = [x['close'] for x in si.get_data(BASE, start_date=START_DATE).iloc]
    print(f'Calculating {SMA_LENGTH} day SMA of {BASE} for the last {len(base_closing_prices)} trading sessions.')
    base_sma_data_set = calculate_sma(base_closing_prices, SMA_LENGTH)
    
    for ticker in tickers():
        print(f'Pulling {ticker} data from {START_DATE.date()} until {datetime.today().date()} to use as numerator in CRS.')
        closing_prices[ticker] = [x['close'] for x in si.get_data(ticker, start_date=START_DATE).iloc]

        # TODO slice base_closing_prices to be same length as closing_prices
        if len(closing_prices[ticker]) != len(base_closing_prices):
            continue

        print(f'Calculating CRS of {ticker}/{BASE} for the last {len(base_closing_prices)} trading sessions.')
        crs[ticker] = comparative_relative_strength(closing_prices[ticker], base_closing_prices)
        print(f'Calculating {SMA_LENGTH} day SMA of {ticker} for the last {len(base_closing_prices)} trading sessions.')
        closing_sma_data_set = calculate_sma(closing_prices[ticker], SMA_LENGTH)
        print(f'Calculating CRS SMA for the {SMA_LENGTH} SMA data set from the {ticker} and {BASE} data sets.')
        crs_sma[ticker] = calculate_crs_sma(closing_sma_data_set, base_sma_data_set)
        
    derivatives = []
    for k, v in crs.items():
        # Gradient (d2x/dy2) of SYMBOL/BASE is the indicator of uptrend on crs.
        x_crs_points = range(len(crs_sma[k]))

        # TODO currently not correct. This finds the beta of the last year's worth of 20 SMA points
        # need to change to only using last 20 data points to see if crs on the short trend is in an uptrend.
        crs_sma_regression_line = least_squares_fit(x_crs_points, crs_sma[k])
        if crs_sma_regression_line[0] > 0.0:
            print(f'{k}/{BASE} CRS is in an uptrend.')
            longer_sma_points = calculate_sma(closing_prices[k], UPTREND_SMA_LENGTH)
            x_closing_points = range(len(longer_sma_points))
            closing_price_regression_line = least_squares_fit(x_closing_points, longer_sma_points)
            if closing_price_regression_line[0] > 0.0:
                print(f'{k} is in an uptrend based on {UPTREND_SMA_LENGTH} dma.')
                derivatives.append((k, crs_sma_regression_line))

    rankings = reversed(sorted(derivatives, key=lambda x: x[1][0]))
    for index, value in enumerate(rankings):
        print(f'{index+1}. {value[0]}: {value[1][0]}')
