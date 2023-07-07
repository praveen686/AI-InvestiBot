"""
Name:
    resource_manager.py

Purpose:
    This module provides utility functions for stock trading. At the moment
    it only contains a resource_manager class. This class is used to manage
    your money and controlling how much you can use for a stock. 

Author:
    Grant Yul Hur

See also:
    Other modules related to running the stock bot -> lambda_implementation, loop_implementation
"""

from typing import Optional
from datetime import datetime

from alpaca_trade_api import REST

from models import BaseModel

__all__ = (
    'ResourceManager',
)


class ResourceManager:
    """
    This is used to manage the money you have, buy/sell stock,
    and place limits on how much you spend/ your risk.

    Args:
        Money (int): Money that you have
        max_percent (float): Max percent of money you can use for a single stock
        max (float): Max amount of money you can use for a stock
        stock_to_money_ratio (float): 0-1, 1 is all stock, 0 is all cash

    Put restraints on your money.
    """
    def __init__(self,
                 model: BaseModel,
                 maximum: Optional[float]=None,
                 max_percent: float=100.0,
                 stock_to_money_ratio: float= 1.0,
                 api_key: str = "",
                 secret_key: str = "",
                 base_url: str = "https://paper-api.alpaca.markets"
                 ) -> None:
        self.used = 0
        if not max_percent:
            self.max_percent = 1
        if not maximum:
            maximum = float("inf")
        self.qty = maximum
        self.ratio = stock_to_money_ratio

        self.stock_mapping = {}
        self.api = REST(api_key, secret_key, base_url=base_url)
        
        equity = float(self.api.equity)
        buying_power = float(self.api.buying_power)

        # Calculate the total value of your account (including stock)
        self.total = equity + buying_power

    def check(self, stock: str, cost: Optional[float]=None) -> float:
        """
        The purpose of this method is to determine how much money can be used
        for a stock. It takes into account the max, max_percent, and ratio to
        ensure that it does not exceed these metrics.

        Args:
            stock (str): The stock ticker
            money (float): The amount of money you want to use
        
        Returns:
            float: The amount of money you can use
        """

    def check_stock_price(self, symbol):
        stock_to_money_ratio = self.ratio
        max_qty_in_stock = self.qty
        max_percent_in_stock = self.max_percent

        # Get account information
        account = self.get_account()
        cash_balance = float(account.buying_power)

        # Get the current market price
        market_price = self.get_market_price(symbol)

        # Calculate the maximum quantity to buy based on the stock-to-money ratio
        max_qty_based_on_ratio = int(cash_balance / market_price * stock_to_money_ratio)

        # Apply additional constraints
        max_qty = min(max_qty_based_on_ratio, max_qty_in_stock)

        positions = self.get_positions()
        total_market_value = sum([float(position.market_value) for position in positions])

        if total_market_value > 0:
            current_allocation = float(positions[symbol].market_value) / total_market_value
        else:
            current_allocation = 0.0

        # Check if the maximum percentage allocation is reached
        if current_allocation >= max_percent_in_stock:
            max_qty = 0

        return max_qty

    def buy(self, amount: int, ticker: str) -> None:
        """
        This method will allow you to purchase a stock.

        Args:
            amount (int): The amount of stock you want to buy
            ticker (str): The stock ticker
        """
        self.api.submit_order(
            symbol=ticker,
            qty=amount,
            side='buy',
            type='market',
            time_in_force='day',
        )

    def sell(self, amount: Optional[int], ticker: str) -> None:
        """
        This method will allow you to sell a stock.

        Args:
            amount (int): The amount of stock you want to sell
            ticker (str): The stock ticker
        """
        self.api.submit_order(
            symbol=ticker,
            qty=amount,
            side='sell',
            type='market',
            time_in_force='day',
        )

    def update(self):
        portfolio = self.api.list_positions()
        for position in portfolio:
            self.sell(position.symbol)

