# Annual-Return-by-Investment-Time-Frame
This program identifies what investment timeframe guarantees a positive return in the S&P 500 with a Python script using the yfinance API. This program evaluates investment timeframes between 1 and 40 years for all possible timeframes between 1928 and 2023. It calculates the average annual compound rate of return (IRR) for a $1000 monthly investment in the S&P 500 between each timeframe.

It found that for investment lengths between 1 and 20 years, there is at least one point in history when the above investment loses money, although the chance of losing money decreases significantly as the investment length increases, and for timeframes from 21 to 40 years, returns are positive no matter what year the investor starts investing.

This program could improve by considering inflation as a return below inflation is not a gain. It could also take into account dividends as this program only considered gains in value.

![IRRs for different investment time frames](https://github.com/user-attachments/assets/82e21979-19b1-41bb-91c4-af2b4771c7a2)
