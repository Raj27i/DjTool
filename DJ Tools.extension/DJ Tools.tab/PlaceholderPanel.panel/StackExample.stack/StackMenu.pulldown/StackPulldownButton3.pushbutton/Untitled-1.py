"""
===============================================================================
            3 CLOSE BREAKOUT + RETEST WITH PYRAMIDING + MACD FILTER
                            OpenAlgo Trading Bot
===============================================================================
"""

from openalgo import api
import pandas as pd
from datetime import datetime, timedelta, time as dt_time
import threading
import time

# ===============================================================================
# TRADING CONFIGURATION
# ===============================================================================

# API Configuration
API_KEY = "openalgo-apikey"
API_HOST = "http://127.0.0.1:5000"
WS_URL = "ws://127.0.0.1:8765"

# Trade Settings
SYMBOL = "NHPC"              # Stock to trade
EXCHANGE = "NSE"             # Exchange (NSE, BSE, NFO, etc.)
QUANTITY = 1                 # Number of shares per entry
PRODUCT = "MIS"              # MIS (Intraday) or CNC (Delivery)

# Strategy Parameters
CANDLE_TIMEFRAME = "5m"      # 1m, 5m, 15m, 30m, 1h, 1d

# Historical Data Lookback
LOOKBACK_DAYS = 5            # Number of days to fetch historical data (1-30)

# MACD Filter Settings
ENABLE_MACD_FILTER = True    # Enable/disable MACD filter
MACD_FAST = 12               # MACD Fast Length
MACD_SLOW = 26               # MACD Slow Length
MACD_SIGNAL = 9              # MACD Signal Length

# Pyramiding Settings
ENABLE_PYRAMIDING = True     # Enable/disable pyramiding
PYRAMID_PERCENT = 0.5        # Pyramiding trigger percentage
MAX_PYRAMIDS = 1             # Max additional entries (total = this + 1)

# Trailing Stop Settings
ENABLE_TRAILING = True       # Enable/disable trailing stop
TRAIL_PERCENT = 0.5          # Trailing stop percentage
TRAIL_FROM_ENTRY = False     # Trail from entry or only after first pyramid

# Direction Control
ENABLE_LONG = True           # Enable long entries
ENABLE_SHORT = True          # Enable short entries

# Day Selection
TRADE_MONDAY = True
TRADE_TUESDAY = True
TRADE_WEDNESDAY = True
TRADE_THURSDAY = False
TRADE_FRIDAY = False

# Signal Check Interval
SIGNAL_CHECK_INTERVAL = 5    # Check for signals every X seconds

# ===============================================================================
# BREAKOUT RETEST TRADING BOT
# ===============================================================================

class BreakoutRetestBot:
    def __init__(self):
        """Initialize the trading bot"""
        # Initialize API client
        self.client = api(
            api_key=API_KEY,
            host=API_HOST,
            ws_url=WS_URL
        )
        
        # Position tracking
        self.position = None  # "BUY" or "SELL"
        self.entry_price = 0
        self.pyramid_count = 0
        self.breakeven_moved = False
        
        # Stop loss tracking
        self.long_stop_price = 0
        self.short_stop_price = 0
        
        # Pyramiding tracking
        self.next_pyramid_long = 0
        self.next_pyramid_short = 0
        
        # Strategy state variables
        self.first_high = None
        self.first_low = None
        self.first_close = None
        self.first_candle_time = None
        
        # Long setup
        self.close_above_count = 0
        self.collected_high = None
        self.marked_high = None
        self.retest_done_long = False
        
        # Short setup
        self.close_below_count = 0
        self.collected_low = None
        self.marked_low = None
        self.retest_done_short = False
        
        # Entry tracking
        self.entered = False
        self.current_day = None
        
        # Real-time price tracking
        self.ltp = None
        self.exit_in_progress = False
        
        # Thread control
        self.running = True
        self.stop_event = threading.Event()
        
        # Instrument for WebSocket
        self.instrument = [{"exchange": EXCHANGE, "symbol": SYMBOL}]
        
        # Strategy name
        self.strategy_name = "Breakout_Retest"
        
        # Validate lookback period
        if LOOKBACK_DAYS < 1:
            print("[WARNING] LOOKBACK_DAYS too small, setting to 1")
            self.lookback_days = 1
        elif LOOKBACK_DAYS > 30:
            print("[WARNING] LOOKBACK_DAYS too large, setting to 30")
            self.lookback_days = 30
        else:
            self.lookback_days = LOOKBACK_DAYS
        
        print("[BOT] OpenAlgo Trading Bot Started")
        print(f"[BOT] Strategy: 3 Close Breakout + Retest with MACD Filter")
        print(f"[BOT] Long Enabled: {ENABLE_LONG} | Short Enabled: {ENABLE_SHORT}")
        print(f"[BOT] Pyramiding: {ENABLE_PYRAMIDING} (Max: {MAX_PYRAMIDS})")
        print(f"[BOT] Trailing Stop: {ENABLE_TRAILING} ({TRAIL_PERCENT}%)")
    
    # ===============================================================================
    # HELPER METHODS
    # ===============================================================================
    
    def is_allowed_day(self):
        """Check if today is in the allowed trading days"""
        weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        if weekday == 0 and TRADE_MONDAY:
            return True
        if weekday == 1 and TRADE_TUESDAY:
            return True
        if weekday == 2 and TRADE_WEDNESDAY:
            return True
        if weekday == 3 and TRADE_THURSDAY:
            return True
        if weekday == 4 and TRADE_FRIDAY:
            return True
        
        return False
    
    def can_enter_now(self):
        """Check if we can enter a trade (before 2:00 PM)"""
        current_time = datetime.now().time()
        cutoff_time = dt_time(14, 0)  # 2:00 PM
        return current_time <= cutoff_time
    
    def is_new_day(self):
        """Check if it's a new trading day"""
        today = datetime.now().date()
        if self.current_day != today:
            return True
        return False
    
    def reset_daily_state(self):
        """Reset strategy state for a new day"""
        print(f"\n[RESET] New trading day: {datetime.now().date()}")
        
        # Move stop to breakeven for overnight positions
        if self.position == "BUY":
            self.long_stop_price = self.entry_price
            print(f"[INFO] Moved long stop to breakeven: {self.entry_price}")
        elif self.position == "SELL":
            self.short_stop_price = self.entry_price
            print(f"[INFO] Moved short stop to breakeven: {self.entry_price}")
        else:
            # Reset everything if no position
            self.long_stop_price = 0
            self.short_stop_price = 0
            self.entry_price = 0
            self.pyramid_count = 0
            self.breakeven_moved = False
            self.next_pyramid_long = 0
            self.next_pyramid_short = 0
        
        # Reset strategy variables
        self.first_high = None
        self.first_low = None
        self.first_close = None
        self.first_candle_time = None
        
        self.close_above_count = 0
        self.collected_high = None
        self.marked_high = None
        self.retest_done_long = False
        
        self.close_below_count = 0
        self.collected_low = None
        self.marked_low = None
        self.retest_done_short = False
        
        self.entered = False
        self.current_day = datetime.now().date()
    
    def calculate_macd(self, data):
        """Calculate MACD using SMA"""
        fast_sma = data['close'].rolling(window=MACD_FAST).mean()
        slow_sma = data['close'].rolling(window=MACD_SLOW).mean()
        macd_line = fast_sma - slow_sma
        signal_line = macd_line.rolling(window=MACD_SIGNAL).mean()
        
        return macd_line, signal_line
    
    # ===============================================================================
    # WEBSOCKET HANDLER
    # ===============================================================================
    
    def on_ltp_update(self, data):
        """Handle real-time LTP updates"""
        if data.get("type") == "market_data" and data.get("symbol") == SYMBOL:
            self.ltp = float(data["data"]["ltp"])
            
            current_time = datetime.now().strftime("%H:%M:%S")
            
            if self.position and not self.exit_in_progress:
                # Calculate real-time P&L
                if self.position == "BUY":
                    unrealized_pnl = (self.ltp - self.entry_price) * QUANTITY * (self.pyramid_count + 1)
                else:
                    unrealized_pnl = (self.entry_price - self.ltp) * QUANTITY * (self.pyramid_count + 1)
                
                pnl_sign = "+" if unrealized_pnl > 0 else "-"
                
                # Determine active stop
                active_stop = self.long_stop_price if self.position == "BUY" else self.short_stop_price
                
                print(f"\r[{current_time}] LTP: Rs.{self.ltp:.2f} | "
                      f"{self.position} @ Rs.{self.entry_price:.2f} | "
                      f"Pyramids: {self.pyramid_count} | "
                      f"P&L: {pnl_sign}Rs.{abs(unrealized_pnl):.2f} | "
                      f"Stop: {active_stop:.2f}    ", end="")
                
                # Check for stop loss hit
                exit_reason = None
                
                if self.position == "BUY" and self.ltp <= self.long_stop_price:
                    exit_reason = "STOPLOSS HIT"
                    print(f"\n[ALERT] STOPLOSS HIT! LTP Rs.{self.ltp:.2f} <= SL Rs.{self.long_stop_price:.2f}")
                
                elif self.position == "SELL" and self.ltp >= self.short_stop_price:
                    exit_reason = "STOPLOSS HIT"
                    print(f"\n[ALERT] STOPLOSS HIT! LTP Rs.{self.ltp:.2f} >= SL Rs.{self.short_stop_price:.2f}")
                
                # Update trailing stop if enabled
                if ENABLE_TRAILING and (TRAIL_FROM_ENTRY or self.pyramid_count > 0):
                    if self.position == "BUY":
                        new_stop = self.ltp * (1 - TRAIL_PERCENT / 100)
                        if new_stop > self.long_stop_price:
                            self.long_stop_price = round(new_stop, 2)
                    
                    elif self.position == "SELL":
                        new_stop = self.ltp * (1 + TRAIL_PERCENT / 100)
                        if new_stop < self.short_stop_price:
                            self.short_stop_price = round(new_stop, 2)
                
                # Place exit order if stop hit
                if exit_reason and not self.exit_in_progress:
                    self.exit_in_progress = True
                    print(f"[EXIT] Placing exit order immediately...")
                    
                    exit_thread = threading.Thread(
                        target=self.place_exit_order,
                        args=(exit_reason,)
                    )
                    exit_thread.start()
            
            elif not self.position:
                status = f"Mode: L:{ENABLE_LONG} S:{ENABLE_SHORT} | Pyramiding: {ENABLE_PYRAMIDING}"
                print(f"\r[{current_time}] LTP: Rs.{self.ltp:.2f} | No Position | {status}    ", end="")
    
    def websocket_thread(self):
        """WebSocket thread for real-time price updates"""
        try:
            print("[WEBSOCKET] Connecting...")
            self.client.connect()
            
            self.client.subscribe_ltp(self.instrument, on_data_received=self.on_ltp_update)
            print(f"[WEBSOCKET] Connected - Monitoring {SYMBOL} in real-time")
            
            while not self.stop_event.is_set():
                time.sleep(1)
                
        except Exception as e:
            print(f"\n[ERROR] WebSocket error: {e}")
        finally:
            print("\n[WEBSOCKET] Closing connection...")
            try:
                self.client.unsubscribe_ltp(self.instrument)
                self.client.disconnect()
            except:
                pass
            print("[WEBSOCKET] Connection closed")
    
    # ===============================================================================
    # DATA AND SIGNAL PROCESSING
    # ===============================================================================
    
    def get_historical_data(self):
        """Fetch historical candle data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            data = self.client.history(
                symbol=SYMBOL,
                exchange=EXCHANGE,
                interval=CANDLE_TIMEFRAME,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if data is not None and len(data) > 0:
                return data
            else:
                print("[WARNING] No data received from API")
                return None
            
        except Exception as e:
            print(f"\n[ERROR] Failed to fetch data: {str(e)}")
            return None
    
    def process_first_candle(self, data):
        """Identify and mark the first candle of the day (9:15 AM)"""
        if data is None or len(data) == 0:
            return
        
        # Try to find the first candle (9:15 AM)
        for idx, row in data.iterrows():
            try:
                # Parse the datetime
                if 'datetime' in data.columns:
                    candle_time = pd.to_datetime(row['datetime'])
                elif 'date' in data.columns:
                    candle_time = pd.to_datetime(row['date'])
                else:
                    continue
                
                # Check if it's 9:15 AM
                if candle_time.hour == 9 and candle_time.minute == 15:
                    if self.first_high is None:  # Only set once per day
                        self.first_high = row['high']
                        self.first_low = row['low']
                        self.first_close = row['close']
                        self.first_candle_time = candle_time
                        print(f"\n[FIRST CANDLE] High: {self.first_high:.2f} | Low: {self.first_low:.2f}")
                    break
            except:
                continue
    
    def check_for_signal(self, data):
        """Check for breakout and retest signals"""
        if data is None or len(data) == 0:
            return None
        
        if self.first_high is None or self.first_low is None:
            return None
        
        # Calculate MACD if filter is enabled
        macd_long_ok = True
        macd_short_ok = True
        
        if ENABLE_MACD_FILTER:
            macd_line, signal_line = self.calculate_macd(data)
            if len(macd_line) > 0 and len(signal_line) > 0:
                macd_long_ok = macd_line.iloc[-1] > signal_line.iloc[-1]
                macd_short_ok = macd_line.iloc[-1] < signal_line.iloc[-1]
        
        # Get recent candles
        recent_candles = data.tail(10)
        
        # === LONG SETUP ===
        if ENABLE_LONG and not self.entered and not self.retest_done_long:
            # Count closes above first high
            for idx, row in recent_candles.iterrows():
                if row['close'] > self.first_high:
                    self.close_above_count += 1
                    if self.collected_high is None:
                        self.collected_high = row['high']
                    else:
                        self.collected_high = max(self.collected_high, row['high'])
            
            # Check for retest after 3 closes above
            if self.close_above_count >= 3:
                for idx, row in recent_candles.iterrows():
                    if row['low'] <= self.first_high:
                        self.marked_high = self.collected_high
                        self.retest_done_long = True
                        print(f"[SETUP] Long retest done. Marked High: {self.marked_high:.2f}")
                        break
        
        # Check for long entry
        if self.retest_done_long and self.marked_high is not None:
            current_close = data['close'].iloc[-1]
            if current_close > self.marked_high and not self.entered and macd_long_ok:
                return "BUY"
        
        # === SHORT SETUP ===
        if ENABLE_SHORT and not self.entered and not self.retest_done_short:
            # Count closes below first low
            for idx, row in recent_candles.iterrows():
                if row['close'] < self.first_low:
                    self.close_below_count += 1
                    if self.collected_low is None:
                        self.collected_low = row['low']
                    else:
                        self.collected_low = min(self.collected_low, row['low'])
            
            # Check for retest after 3 closes below
            if self.close_below_count >= 3:
                for idx, row in recent_candles.iterrows():
                    if row['high'] >= self.first_low:
                        self.marked_low = self.collected_low
                        self.retest_done_short = True
                        print(f"[SETUP] Short retest done. Marked Low: {self.marked_low:.2f}")
                        break
        
        # Check for short entry
        if self.retest_done_short and self.marked_low is not None:
            current_close = data['close'].iloc[-1]
            if current_close < self.marked_low and not self.entered and macd_short_ok:
                return "SELL"
        
        return None
    
    def check_pyramid_signal(self):
        """Check if pyramiding condition is met"""
        if not ENABLE_PYRAMIDING or self.pyramid_count >= MAX_PYRAMIDS:
            return None
        
        if not self.can_enter_now():
            return None
        
        if self.ltp is None:
            return None
        
        if self.position == "BUY" and self.ltp >= self.next_pyramid_long:
            return "BUY"
        
        if self.position == "SELL" and self.ltp <= self.next_pyramid_short:
            return "SELL"
        
        return None
    
    # ===============================================================================
    # ORDER EXECUTION
    # ===============================================================================
    
    def get_executed_price(self, order_id):
        """Get actual executed price from order status"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            time.sleep(2)
            
            try:
                response = self.client.orderstatus(
                    order_id=order_id,
                    strategy=self.strategy_name
                )
                
                if response.get("status") == "success":
                    order_data = response.get("data", {})
                    
                    if order_data.get("order_status") == "complete":
                        executed_price = float(order_data.get("average_price", 0))
                        if executed_price > 0:
                            return executed_price
                    
                    elif order_data.get("order_status") in ["rejected", "cancelled"]:
                        print(f"[ERROR] Order {order_data.get('order_status')}")
                        return None
                    
                    else:
                        print(f"[WAITING] Order status: {order_data.get('order_status')}")
                
            except Exception as e:
                print(f"[ERROR] Failed to get order status: {e}")
        
        return None
    
    def place_entry_order(self, signal):
        """Place entry order"""
        print(f"\n[ORDER] Placing {signal} order for {QUANTITY} shares of {SYMBOL}")
        
        try:
            response = self.client.placeorder(
                strategy=self.strategy_name,
                symbol=SYMBOL,
                exchange=EXCHANGE,
                action=signal,
                quantity=QUANTITY,
                price_type="MARKET",
                product=PRODUCT
            )
            
            if response.get("status") == "success":
                order_id = response.get("orderid")
                print(f"[ORDER] Order placed. ID: {order_id}")
                
                executed_price = self.get_executed_price(order_id)
                
                if executed_price:
                    self.position = signal
                    self.entry_price = executed_price
                    self.pyramid_count = 0
                    self.breakeven_moved = False
                    
                    # Set initial stop loss
                    if signal == "BUY":
                        self.long_stop_price = self.first_low
                        self.short_stop_price = 0
                        self.next_pyramid_long = round(self.entry_price * (1 + PYRAMID_PERCENT / 100), 2)
                    else:  # SELL
                        self.short_stop_price = self.first_high
                        self.long_stop_price = 0
                        self.next_pyramid_short = round(self.entry_price * (1 - PYRAMID_PERCENT / 100), 2)
                    
                    self.entered = True
                    
                    print("\n" + "="*60)
                    print(" TRADE EXECUTED")
                    print("="*60)
                    print(f" Position: {signal}")
                    print(f" Entry Price: Rs.{self.entry_price:.2f}")
                    print(f" Quantity: {QUANTITY}")
                    if signal == "BUY":
                        print(f" Stop Loss: Rs.{self.long_stop_price:.2f}")
                        print(f" Next Pyramid: Rs.{self.next_pyramid_long:.2f}")
                    else:
                        print(f" Stop Loss: Rs.{self.short_stop_price:.2f}")
                        print(f" Next Pyramid: Rs.{self.next_pyramid_short:.2f}")
                    print("="*60)
                    
                    self.exit_in_progress = False
                    return True
                else:
                    print("[ERROR] Could not get executed price")
            else:
                print(f"[ERROR] Order failed: {response}")
                
        except Exception as e:
            print(f"[ERROR] Failed to place order: {e}")
        
        return False
    
    def place_pyramid_order(self, signal):
        """Place pyramiding order"""
        self.pyramid_count += 1
        print(f"\n[PYRAMID] Adding position #{self.pyramid_count + 1}")
        
        try:
            response = self.client.placeorder(
                strategy=self.strategy_name,
                symbol=SYMBOL,
                exchange=EXCHANGE,
                action=signal,
                quantity=QUANTITY,
                price_type="MARKET",
                product=PRODUCT
            )
            
            if response.get("status") == "success":
                order_id = response.get("orderid")
                print(f"[PYRAMID] Order placed. ID: {order_id}")
                
                executed_price = self.get_executed_price(order_id)
                
                if executed_price:
                    # Move stop to breakeven after first pyramid
                    if not self.breakeven_moved:
                        if signal == "BUY":
                            self.long_stop_price = self.entry_price
                        else:
                            self.short_stop_price = self.entry_price
                        self.breakeven_moved = True
                        print(f"[INFO] Stop moved to breakeven: Rs.{self.entry_price:.2f}")
                    
                    # Set next pyramid level
                    if signal == "BUY":
                        self.next_pyramid_long = round(executed_price * (1 + PYRAMID_PERCENT / 100), 2)
                        print(f"[INFO] Next pyramid level: Rs.{self.next_pyramid_long:.2f}")
                    else:
                        self.next_pyramid_short = round(executed_price * (1 - PYRAMID_PERCENT / 100), 2)
                        print(f"[INFO] Next pyramid level: Rs.{self.next_pyramid_short:.2f}")
                    
                    return True
                
            else:
                print(f"[ERROR] Pyramid order failed: {response}")
                self.pyramid_count -= 1  # Revert count on failure
                
        except Exception as e:
            print(f"[ERROR] Failed to place pyramid order: {e}")
            self.pyramid_count -= 1
        
        return False
    
    def place_exit_order(self, reason="Manual"):
        """Place exit order for all positions"""
        if not self.position:
            self.exit_in_progress = False
            return
        
        exit_action = "SELL" if self.position == "BUY" else "BUY"
        total_qty = QUANTITY * (self.pyramid_count + 1)
        
        print(f"\n[EXIT] Closing {self.position} position - {reason}")
        print(f"[EXIT] Total quantity to exit: {total_qty}")
        
        try:
            response = self.client.placeorder(
                strategy=self.strategy_name,
                symbol=SYMBOL,
                exchange=EXCHANGE,
                action=exit_action,
                quantity=total_qty,
                price_type="MARKET",
                product=PRODUCT
            )
            
            if response.get("status") == "success":
                order_id = response.get("orderid")
                print(f"[EXIT] Exit order placed. ID: {order_id}")
                
                exit_price = self.get_executed_price(order_id)
                
                if exit_price:
                    # Calculate P&L
                    if self.position == "BUY":
                        pnl = (exit_price - self.entry_price) * total_qty
                    else:
                        pnl = (self.entry_price - exit_price) * total_qty
                    
                    print("\n" + "="*60)
                    print(" POSITION CLOSED")
                    print("="*60)
                    print(f" Reason: {reason}")
                    print(f" Exit Price: Rs.{exit_price:.2f}")
                    print(f" Entry Price: Rs.{self.entry_price:.2f}")
                    print(f" Total Quantity: {total_qty}")
                    print(f" Pyramids: {self.pyramid_count}")
                    print(f" P&L: Rs.{pnl:.2f} [{('PROFIT' if pnl > 0 else 'LOSS')}]")
                    print("="*60)
                else:
                    print("[WARNING] Exit order placed but could not confirm price")
                
                # Reset position
                self.position = None
                self.entry_price = 0
                self.pyramid_count = 0
                self.breakeven_moved = False
                self.long_stop_price = 0
                self.short_stop_price = 0
                self.next_pyramid_long = 0
                self.next_pyramid_short = 0
                self.exit_in_progress = False
                
            else:
                print(f"[ERROR] Exit order failed: {response}")
                self.exit_in_progress = False
                
        except Exception as e:
            print(f"[ERROR] Failed to exit: {e}")
            self.exit_in_progress = False
    
    # ===============================================================================
    # STRATEGY THREAD
    # ===============================================================================
    
    def strategy_thread(self):
        """Main strategy logic thread"""
        print("[STRATEGY] Strategy thread started")
        print(f"[STRATEGY] Checking signals every {SIGNAL_CHECK_INTERVAL} seconds")
        
        while not self.stop_event.is_set():
            try:
                # Check for new day and reset
                if self.is_new_day():
                    self.reset_daily_state()
                
                # Check if today is allowed for trading
                if not self.is_allowed_day():
                    time.sleep(60)
                    continue
                
                # Check for EOD exit (3:25 PM)
                current_time = datetime.now().time()
                if current_time >= dt_time(15, 25) and self.position:
                    print("\n[EOD] End of day - closing all positions")
                    self.place_exit_order("End of Day")
                
                # Fetch historical data
                data = self.get_historical_data()
                
                if data is not None:
                    # Process first candle if not done
                    if self.first_high is None:
                        self.process_first_candle(data)
                    
                    # Look for entry signals if no position
                    if not self.position and not self.exit_in_progress:
                        if self.can_enter_now():
                            signal = self.check_for_signal(data)
                            if signal:
                                self.place_entry_order(signal)
                    
                    # Look for pyramid signals if in position
                    elif self.position and ENABLE_PYRAMIDING:
                        pyramid_signal = self.check_pyramid_signal()
                        if pyramid_signal:
                            self.place_pyramid_order(pyramid_signal)
                
                # Sleep before next check
                time.sleep(SIGNAL_CHECK_INTERVAL)
                
            except Exception as e:
                print(f"\n[ERROR] Strategy error: {e}")
                time.sleep(10)
    
    # ===============================================================================
    # MAIN RUN METHOD
    # ===============================================================================
    
    def run(self):
        """Main method to run the bot"""
        print("="*60)
        print(" 3 CLOSE BREAKOUT + RETEST STRATEGY")
        print("="*60)
        print(f" Symbol: {SYMBOL} | Exchange: {EXCHANGE}")
        print(f" Long: {ENABLE_LONG} | Short: {ENABLE_SHORT}")
        print(f" Pyramiding: {ENABLE_PYRAMIDING} (Max: {MAX_PYRAMIDS})")
        print(f" Trailing: {ENABLE_TRAILING} ({TRAIL_PERCENT}%)")
        print(f" MACD Filter: {ENABLE_MACD_FILTER}")
        print(f" Timeframe: {CANDLE_TIMEFRAME}")
        print(f" Lookback: {self.lookback_days} days")
        print("="*60)
        
        # Trading days
        days = []
        if TRADE_MONDAY: days.append("Mon")
        if TRADE_TUESDAY: days.append("Tue")
        if TRADE_WEDNESDAY: days.append("Wed")
        if TRADE_THURSDAY: days.append("Thu")
        if TRADE_FRIDAY: days.append("Fri")
        print(f" Trading Days: {', '.join(days)}")
        print("="*60)
        print("\nPress Ctrl+C to stop the bot\n")
        
        # Start WebSocket thread
        ws_thread = threading.Thread(target=self.websocket_thread, daemon=True)
        ws_thread.start()
        
        time.sleep(2)
        
        # Start strategy thread
        strat_thread = threading.Thread(target=self.strategy_thread, daemon=True)
        strat_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Shutting down bot...")
            self.running = False
            self.stop_event.set()
            
            if self.position and not self.exit_in_progress:
                print("[INFO] Closing open position before shutdown...")
                self.place_exit_order("Bot Shutdown")
            
            ws_thread.join(timeout=5)
            strat_thread.join(timeout=5)
            
            print("[SUCCESS] Bot stopped successfully!")

# ===============================================================================
# START THE BOT
# ===============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print(" BREAKOUT RETEST STRATEGY - READY TO RUN")
    print("="*60)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Long: {ENABLE_LONG} | Short: {ENABLE_SHORT}")
    print(f" Pyramiding: {ENABLE_PYRAMIDING}")
    print("="*60 + "\n")
    
    bot = BreakoutRetestBot()
    bot.run()