#region imports
from AlgorithmImports import *
#endregion

########################################################################################
#                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                      #
# you may not use this file except in compliance with the License.                     #
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0   #
#                                                                                      #
# Unless required by applicable law or agreed to in writing, software                  #
# distributed under the License is distributed on an "AS IS" BASIS,                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.             #
# See the License for the specific language governing permissions and                  #
# limitations under the License.                                                       #
#                                                                                      #
# Copyright [2021] [Rocco Claudio Cannizzaro]                                          #
#                                                                                      #
########################################################################################

import numpy as np
import pandas as pd
import time as timer
from System.Drawing import Color
from Strategies import *
from Logger import *

# #####################################
#    Backtesting parameters
# #####################################
def initialize(self):
   # Backtesting period
   self.SetStartDate(2021, 1, 1)
   self.SetEndDate(2021, 11, 30)
   # Store the initial account value
   self.initialAccountValue = 1000000
   self.SetCash(self.initialAccountValue)

   # Logging level: 
   #  -> 0 = ERROR
   #  -> 1 = WARNING
   #  -> 2 = INFO
   #  -> 3 = DEBUG
   #  -> 4 = TRACE (Attention!! This can consume your entire daily log limit)
   self.logLevel = 2

   # Ticker Symbol
   self.ticker = "SPX"

   # Days to Expiration
   self.dte = 45
   # The size of the window used to filter the option chain: options expiring in the range [dte-dteWindow, dte] will be selected
   self.dteWindow = 7

   # Risk Free Rate for the Black-Scholes-Merton model
   self.riskFreeRate = 0.001

   # Use Limit Orders to open/close a position?
   self.useLimitOrders = True

   # Slippage used to set Limit orders
   self.slippage = 0.05
         
   # Adjustment factor applied to the Mid-Price to set the Limit Order:
   #  - Credit Strategy:
   #      Adj = 0.3 --> sets the Limit Order price 30% higher than the current Mid-Price
   #  - Debit Strategy:
   #      Adj = -0.2 --> sets the Limit Order price 20% lower than the current Mid-Price
   self.limitOrderRelativePriceAdjustment = 0.2

   # Alternative method to set the absolute price (per contract) of the Limit Order. This method is used if a number is specified
   # Unless you know that your price target can get a fill, it is advisable to use a relative adjustment or you may never get your order filled 
   #  - Credit Strategy:
   #      AbsolutePrice = 1.5 --> sets the Limit Order price at exactly 1.5$
   #  - Debit Strategy:
   #      AbsolutePrice = -2.3 --> sets the Limit Order price at exactly -2.3$
   # self.limitOrderAbsolutePrice = 2.1

   # Set expiration for Limit orders
   self.limitOrderExpiration = timedelta(hours = 4)

   # Target <credit|debit> premium amount: used to determine the number of contracts needed to reach the desired target amount
   #  - targetPremiumPct --> target premium is expressed as a percentage of the total Portfolio Net Liq (0 < targetPremiumPct < 1)
   #  - targetPremium --> target premium is a fixed dollar amount
   # If both are specified, targetPremiumPct takes precedence. If none of them are specified, the number of contracts specified by the maxOrderQuantity parameter is used.
   self.targetPremiumPct = None
   self.targetPremium = 1000

   # Maximum quantity used to scale each position. If the target premium cannot be reached within this quantity (i.e. premium received is too low), the position is not going to be opened
   self.maxOrderQuantity = 20
   # If True, the order is submitted as long as it does not exceed the maxOrderQuantity.
   self.validateQuantity = True

   # Profit Target Factor (Multiplier of the premium received/paid when the position was opened)
   self.profitTarget = 0.6

   # Defines how the profit target is calculated. Valid options are (case insensitive):
   # - Premium: the profit target is a percentage of the premium paid/received. 
   # - Theta: the profit target is calculated based on the theta value of the position evaluated at self.thetaProfitDays from the time of entering the trade
   # - TReg: the profit target is calculated as a percentage of the TReg (MaxLoss + openPremium)
   # - Margin: the profit target is calculted as a percentage of the margin requirement (calculated based on self.portfolioMarginStress percentage upside/downside movement of the underlying)
   self.profitTargetMethod = "Premium"
   # Number of days into the future at which the theta of the position is calculated. Used if profitTargetMethod = "Theta"
   self.thetaProfitDays = None
   # Upside/Downside stress applied to the underlying to calculate the portfolio margin requirement of the position
   self.portfolioMarginStress = 0.12


   # Stop Loss Multiplier, expressed as a function of the profit target (rather than the credit received)
   # The position is closed (Market Order) if:
   #    Position P&L < -abs(openPremium) * stopLossMultiplier
   # where:
   #  - openPremium is the premium received (positive) in case of credit strategies
   #  - openPremium is the premium paid (negative) in case of debit strategies
   #
   # Credit Strategies (i.e. $2 credit):
   #  - profitTarget < 1 (i.e. 0.5 -> 50% profit target -> $1 profit)
   #  - stopLossMultiplier = 2 * profitTarget (i.e. -abs(openPremium) * stopLossMultiplier = -abs(2) * 2 * 0.5 = -2 --> stop if P&L < -2$)
   # Debit Strategies (i.e. $4 debit):
   #  - profitTarget < 1 (i.e. 0.5 -> 50% profit target -> $2 profit)
   #  - stopLossMultiplier < 1 (You can't lose more than the debit paid. i.e. stopLossMultiplier = 0.6 --> stop if P&L < -2.4$)
   self.stopLossMultiplier = 2 * self.profitTarget
   #self.stopLossMultiplier = 0.6

   # DTE Threshold. This is ignored if self.dte < self.dteThreshold
   self.dteThreshold = None
   # DIT Threshold. This is ignored if self.dte < self.ditThreshold
   self.ditThreshold = None
   self.hardDitThreshold = None

   # Controls what happens when an open position reaches/crosses the dteThreshold ( -> DTE(openPosition) <= dteThreshold)
   # - If True, the position is closed as soon as the dteThreshold is reached, regardless of whether the position is profitable or not
   # - If False, once the dteThreshold is reached, the position is closed as soon as it is profitable
   self.forceDteThreshold = False
   # Controls what happens when an open position reaches/crosses the ditThreshold ( -> DIT(openPosition) >= ditThreshold)
   # - If True, the position is closed as soon as the ditThreshold is reached, regardless of whether the position is profitable or not
   # - If False, once the ditThreshold is reached, the position is closed as soon as it is profitable
   # - If self.hardDitThreashold is set, the position is closed once the hardDitThreashold is crossed, regardless of whether forceDitThreshold is True or False
   self.forceDitThreshold = False
         
   # Maximum number of open positions at any given time
   self.maxActivePositions = 20

   # If True, the order mid-price is validated to make sure the Bid-Ask spread is not too wide.
   #  - The order is not submitted if the ratio between Bid-Ask spread of the entire order and its mid-price is more than self.bidAskSpreadRatio
   self.validateBidAskSpread = False
   self.bidAskSpreadRatio = 0.8

   #Controls whether to include Cancelled orders (Limit orders that didn't fill) in the final output
   self.includeCancelledOrders = False

   # Controls whether to allow multiple positions to be opened for the same Expiration date
   self.allowMultipleEntriesPerExpiry = False

   # Controls whether to include details on each leg (open/close fill price and descriptive statistics about mid-price, Greeks, and IV)
   self.includeLegDetails = False
   # Specify which Greeks should be included in the trade log (Set an empty list if you don't want any of the greeks)
   self.greeksIncluded = ["Delta", "Gamma", "Vega", "Theta", "Rho", "Vomma", "Elasticity"]
   # self.greeksIncluded = []

   # Controls whether to track the details on each leg across the life of the trade (it generates a separate csv in the log with leg details at regular time intervals)
   self.trackLegDetails = False
   # The frequency (in minutes) with which the leg details are updated (used only if includeLegDetails = True). 
   # Updating with high frequency (i.e. every 5 minutes) will slow down the execution
   self.legDatailsUpdateFrequency = 15

   # The frequency (in minutes) with which each position is managed
   self.managePositionFrequency = 30

   # Controls whether to use the furthest (True) or the earliest (False) expiration date when multiple expirations are available in the chain
   self.useFurthestExpiry = True
   # Controls whether to consider the DTE of the last closed position when opening a new one:
   # If True, the Expiry date of the new position is selected such that the open DTE is the nearest to the DTE of the closed position
   self.dynamicDTESelection = False

   # Minimum time distance between opening two consecutive trades
   self.minimumTradeScheduleDistance = timedelta(days = 1)


   # ########################################################################
   # Trading Strategies. 
   #   - Multiple strategies can be executed at the same time
   #   - Each strategy is processed indipendently of the others
   #   - New strategies can be created by extending the OptionStrategy class and implementing the getOrder method
   # Parameters details:
   #   - Net Delta: Used for Straddle, IronFly and Butterfly strategy. 
   #      - If netDelta = None        --> the Strategy will be centered around the ATM strike
   #      - If netDelta = n (-50, 50) --> the strike selection will be centered in a way to achieve the requested net delta exposure

   # ########################################################################

   # Holds all the strategies to be executed
   self.strategies = []

   # self.strategies.append(PutStrategy(self, delta = 10, creditStrategy = True))
   # self.strategies.append(CallStrategy(self, delta = 10, creditStrategy = True))
   # self.strategies.append(StraddleStrategy(self, name = "Straddle", netDelta = None, creditStrategy = True))
   # self.strategies.append(StrangleStrategy(self, name = "Strangle", putDelta = 10, callDelta = 10, creditStrategy = True))
   self.strategies.append(PutSpreadStrategy(self, name = "PS", delta = 10, wingSize = 25, creditStrategy = True))
   self.strategies.append(CallSpreadStrategy(self, name = "CS", delta = 10, wingSize = 25, creditStrategy = True))
   # self.strategies.append(IronCondorStrategy(self, name = "IC", putDelta = 10, callDelta = 10, putWingSize = 10, callWingSize = 10, creditStrategy = True))
   # self.strategies.append(IronFlyStrategy(self, name = "IF", netDelta = None, putWingSize = 10, callWingSize = 10, creditStrategy = True))
   # self.strategies.append(ButterflyStrategy(self, name = "Bfly", butteflyType = "Put", netDelta = None, butterflyLeftWingSize = 10, butterflyRightWingSize = 10, creditStrategy = True))
   # self.strategies.append(TEBombShelterStrategy(self, name = "TEBS", delta = 15, frontDte = self.dte - 30, hedgeAllocation = 0.1, chartUpdateFrequency = 5))
   # self.strategies.append(CustomStrategy(self
   #                                       , name = "BWB"
   #                                       , deltas = [50, 30, 10]
   #                                       , types = "Put"
   #                                       , sides = [1, -2, 1]
   #                                       , sidesDesc = ["Delta50Put", "Delta30Put", "Delta10Put"]
   #                                       , creditStrategy = None
   #                                       ))

   # Coarse filter for the Universe selection. It selects nStrikes on both sides of the ATM strike for each available expiration
   self.nStrikesLeft = 200
   self.nStrikesRight = 200

   # Time Resolution
   self.timeResolution = Resolution.Minute   # Resolution.Minute .Hour .Daily

   # Set brokerage model and margin account
   self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

   # The start time at which the algorithm will start scheduling the strategy execution (to open new positions). No positions will be opened before this time
   self.scheduleStartTime = time(9, 45, 0)
   # Periodic interval with which the algorithm will check to open new positions
   self.scheduleFrequency = timedelta(hours = 1)

   # Setup the backtesting algorithm
   self.setupBacktest()

   # Setup the charts. Use the following flags to disable certain charts:
   # PnL = False, Performance = False, WinLossStats = False, LossDetails = False
   self.setupCharts()
