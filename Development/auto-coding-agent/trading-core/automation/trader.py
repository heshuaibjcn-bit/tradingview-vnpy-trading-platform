"""
同花顺自动化交易模块
Automation Trader Module for Tonghuashun
"""

import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

import numpy as np
import cv2
import pyautogui

from config.settings import settings
from utils.logger import logger
from .window import (
    find_tonghuashun_window,
    bring_window_to_front,
    screenshot_window,
    screenshot_screen,
    TemplateMatcher,
    CoordinateManager,
    matcher,
    coord_manager,
)
from .screenshot import ScreenshotManager, screenshot_manager


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type"""
    LIMIT = "limit"  # 限价单
    MARKET = "market"  # 市价单


class TradingError(Exception):
    """Trading operation error"""
    pass


class TradingResult:
    """Trading operation result"""

    def __init__(
        self,
        success: bool,
        action: str,
        message: str = "",
        screenshot_path: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.action = action
        self.message = message
        self.screenshot_path = screenshot_path
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "action": self.action,
            "message": self.message,
            "screenshot_path": str(self.screenshot_path) if self.screenshot_path else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        return f"TradingResult(success={self.success}, action='{self.action}', message='{self.message}')"


class THSTrader:
    """
    Tonghuashun (同花顺) Automated Trader

    Automates trading operations in Tonghuashun trading client
    """

    def __init__(self):
        """Initialize trader"""
        self.window = None
        self.matcher = matcher
        self.coord_manager = coord_manager
        self.screenshot_manager = screenshot_manager
        self.is_logged_in = False

        logger.info("THSTrader initialized")

    def connect(self) -> TradingResult:
        """
        Connect to Tonghuashun window

        Returns:
            TradingResult with connection status
        """
        logger.info("Connecting to Tonghuashun window...")

        self.window = find_tonghuashun_window()

        if not self.window:
            return TradingResult(
                success=False,
                action="connect",
                message="Tonghuashun window not found. Please make sure it's running."
            )

        # Bring window to front
        if not bring_window_to_front(self.window.hwnd):
            logger.warning("Could not bring window to front, but continuing...")

        time.sleep(0.5)  # Wait for window to settle

        # Take screenshot for verification
        try:
            screenshot = screenshot_window(self.window)
            screenshot_path = self.screenshot_manager.save_log_screenshot(
                screenshot,
                "connect",
                {"action": "connect", "window_title": self.window.title}
            )
            logger.info(f"Connected screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            screenshot_path = None

        logger.info("Successfully connected to Tonghuashun window")
        return TradingResult(
            success=True,
            action="connect",
            message="Successfully connected to Tonghuashun",
            screenshot_path=screenshot_path,
            metadata={"window_title": self.window.title}
        )

    def _find_element(self, template_name: str, threshold: float = 0.8) -> Optional[Tuple[int, int, int, int]]:
        """
        Find UI element by template matching

        Args:
            template_name: Template filename
            threshold: Matching threshold

        Returns:
            (x, y, width, height) or None if not found
        """
        screenshot = screenshot_window(self.window)
        match = self.matcher.find_template(screenshot, template_name, threshold)

        if match:
            logger.debug(f"Element found: {template_name} at {match}")
        else:
            logger.warning(f"Element not found: {template_name}")

        return match

    def _click_at(self, position: Tuple[int, int], button: str = "left", clicks: int = 1) -> None:
        """
        Click at screen position

        Args:
            position: (x, y) screen coordinates
            button: Mouse button ('left', 'right', 'middle')
            clicks: Number of clicks
        """
        x, y = position

        # Convert window-relative to screen coordinates if needed
        screen_x = self.window.rect.left + x if self.window else x
        screen_y = self.window.rect.top + y if self.window else y

        logger.debug(f"Clicking at: ({screen_x}, {screen_y})")

        pyautogui.click(screen_x, screen_y, clicks=clicks, button=button)

        # Small delay after click
        time.sleep(0.2)

    def _type_text(self, text: str, interval: float = 0.01) -> None:
        """
        Type text using keyboard

        Args:
            text: Text to type
            interval: Delay between keystrokes
        """
        logger.debug(f"Typing text: {text}")
        pyautogui.typewrite(text, interval=interval)
        time.sleep(0.2)

    def _press_key(self, key: str, presses: int = 1) -> None:
        """
        Press keyboard key

        Args:
            key: Key name ('enter', 'tab', 'escape', etc.)
            presses: Number of times to press
        """
        logger.debug(f"Pressing key: {key} x{presses}")
        pyautogui.press(key, presses=presses)
        time.sleep(0.2)

    def _wait_for_element(
        self,
        template_name: str,
        timeout: float = 5.0,
        threshold: float = 0.8
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Wait for element to appear

        Args:
            template_name: Template filename
            timeout: Maximum wait time in seconds
            threshold: Matching threshold

        Returns:
            (x, y, width, height) or None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            match = self._find_element(template_name, threshold)
            if match:
                return match
            time.sleep(0.3)

        logger.warning(f"Element wait timeout: {template_name}")
        return None

    def input_stock_code(self, code: str, method: str = "template") -> TradingResult:
        """
        Input stock code

        Args:
            code: Stock code (e.g., "000001" or "600000")
            method: Input method ("template" or "coordinate")

        Returns:
            TradingResult
        """
        logger.info(f"Inputting stock code: {code}")

        if not self.window:
            return TradingResult(False, "input_stock_code", "Not connected to window")

        try:
            # Find stock code input field
            if method == "template":
                # Use template matching to find input field
                coord = self._wait_for_element("stock_code_input", timeout=3.0)
                if not coord:
                    return TradingResult(
                        False,
                        "input_stock_code",
                        "Stock code input field not found"
                    )
                x, y, width, height = coord
                click_pos = (x + width // 2, y + height // 2)
            else:
                # Use saved coordinates
                coord = self.coord_manager.get_coordinate("stock_code_input")
                if not coord:
                    return TradingResult(
                        False,
                        "input_stock_code",
                        "Stock code input coordinates not saved"
                    )
                x, y, width, height = coord
                click_pos = (x + width // 2, y + height // 2)

            # Click input field
            self._click_at(click_pos)
            time.sleep(0.3)

            # Clear existing text (Ctrl+A or Cmd+A, then delete)
            if self.window:  # Windows
                pyautogui.hotkey('ctrl', 'a')
            else:  # macOS
                pyautogui.hotkey('command', 'a')
            time.sleep(0.1)
            self._press_key('backspace')

            # Type stock code
            self._type_text(code)

            # Press Enter to confirm
            self._press_key('enter')
            time.sleep(0.5)

            logger.info(f"Stock code input successful: {code}")
            return TradingResult(
                True,
                "input_stock_code",
                f"Stock code {code} input successfully",
                metadata={"code": code, "method": method}
            )

        except Exception as e:
            logger.error(f"Error inputting stock code: {e}")
            return TradingResult(
                False,
                "input_stock_code",
                f"Error: {str(e)}"
            )

    def input_price(self, price: float) -> TradingResult:
        """
        Input order price

        Args:
            price: Order price

        Returns:
            TradingResult
        """
        logger.info(f"Inputting price: {price}")

        if not self.window:
            return TradingResult(False, "input_price", "Not connected to window")

        try:
            # Find price input field
            coord = self._wait_for_element("price_input", timeout=3.0)
            if not coord:
                return TradingResult(
                    False,
                    "input_price",
                    "Price input field not found"
                )

            x, y, width, height = coord
            click_pos = (x + width // 2, y + height // 2)

            # Click input field
            self._click_at(click_pos)
            time.sleep(0.3)

            # Clear existing text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            self._press_key('backspace')

            # Type price
            price_str = f"{price:.2f}"
            self._type_text(price_str)

            logger.info(f"Price input successful: {price}")
            return TradingResult(
                True,
                "input_price",
                f"Price {price} input successfully",
                metadata={"price": price}
            )

        except Exception as e:
            logger.error(f"Error inputting price: {e}")
            return TradingResult(
                False,
                "input_price",
                f"Error: {str(e)}"
            )

    def input_quantity(self, quantity: int) -> TradingResult:
        """
        Input order quantity

        Args:
            quantity: Order quantity (number of shares)

        Returns:
            TradingResult
        """
        logger.info(f"Inputting quantity: {quantity}")

        if not self.window:
            return TradingResult(False, "input_quantity", "Not connected to window")

        try:
            # Find quantity input field
            coord = self._wait_for_element("quantity_input", timeout=3.0)
            if not coord:
                return TradingResult(
                    False,
                    "input_quantity",
                    "Quantity input field not found"
                )

            x, y, width, height = coord
            click_pos = (x + width // 2, y + height // 2)

            # Click input field
            self._click_at(click_pos)
            time.sleep(0.3)

            # Clear existing text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            self._press_key('backspace')

            # Type quantity
            self._type_text(str(quantity))

            logger.info(f"Quantity input successful: {quantity}")
            return TradingResult(
                True,
                "input_quantity",
                f"Quantity {quantity} input successfully",
                metadata={"quantity": quantity}
            )

        except Exception as e:
            logger.error(f"Error inputting quantity: {e}")
            return TradingResult(
                False,
                "input_quantity",
                f"Error: {str(e)}"
            )

    def click_buy_button(self) -> TradingResult:
        """
        Click buy button

        Returns:
            TradingResult
        """
        logger.info("Clicking buy button")

        if not self.window:
            return TradingResult(False, "click_buy", "Not connected to window")

        try:
            # Find buy button
            coord = self._wait_for_element("buy_button", timeout=3.0)
            if not coord:
                return TradingResult(
                    False,
                    "click_buy",
                    "Buy button not found"
                )

            x, y, width, height = coord
            click_pos = (x + width // 2, y + height // 2)

            # Click buy button
            self._click_at(click_pos)
            time.sleep(0.5)

            # Wait for confirmation dialog
            confirm_coord = self._wait_for_element("confirm_button", timeout=2.0)
            if confirm_coord:
                # Click confirm
                x, y, width, height = confirm_coord
                confirm_pos = (x + width // 2, y + height // 2)
                self._click_at(confirm_pos)
                time.sleep(0.5)

            logger.info("Buy button clicked successfully")
            return TradingResult(
                True,
                "click_buy",
                "Buy order submitted successfully"
            )

        except Exception as e:
            logger.error(f"Error clicking buy button: {e}")
            return TradingResult(
                False,
                "click_buy",
                f"Error: {str(e)}"
            )

    def click_sell_button(self) -> TradingResult:
        """
        Click sell button

        Returns:
            TradingResult
        """
        logger.info("Clicking sell button")

        if not self.window:
            return TradingResult(False, "click_sell", "Not connected to window")

        try:
            # Find sell button
            coord = self._wait_for_element("sell_button", timeout=3.0)
            if not coord:
                return TradingResult(
                    False,
                    "click_sell",
                    "Sell button not found"
                )

            x, y, width, height = coord
            click_pos = (x + width // 2, y + height // 2)

            # Click sell button
            self._click_at(click_pos)
            time.sleep(0.5)

            # Wait for confirmation dialog
            confirm_coord = self._wait_for_element("confirm_button", timeout=2.0)
            if confirm_coord:
                # Click confirm
                x, y, width, height = confirm_coord
                confirm_pos = (x + width // 2, y + height // 2)
                self._click_at(confirm_pos)
                time.sleep(0.5)

            logger.info("Sell button clicked successfully")
            return TradingResult(
                True,
                "click_sell",
                "Sell order submitted successfully"
            )

        except Exception as e:
            logger.error(f"Error clicking sell button: {e}")
            return TradingResult(
                False,
                "click_sell",
                f"Error: {str(e)}"
            )

    def click_cancel_button(self) -> TradingResult:
        """
        Click cancel button

        Returns:
            TradingResult
        """
        logger.info("Clicking cancel button")

        if not self.window:
            return TradingResult(False, "click_cancel", "Not connected to window")

        try:
            # Find cancel button
            coord = self._wait_for_element("cancel_button", timeout=3.0)
            if not coord:
                return TradingResult(
                    False,
                    "click_cancel",
                    "Cancel button not found"
                )

            x, y, width, height = coord
            click_pos = (x + width // 2, y + height // 2)

            # Click cancel button
            self._click_at(click_pos)
            time.sleep(0.5)

            logger.info("Cancel button clicked successfully")
            return TradingResult(
                True,
                "click_cancel",
                "Cancel order submitted successfully"
            )

        except Exception as e:
            logger.error(f"Error clicking cancel button: {e}")
            return TradingResult(
                False,
                "click_cancel",
                f"Error: {str(e)}"
            )

    def buy(
        self,
        code: str,
        price: float,
        quantity: int,
        order_type: OrderType = OrderType.LIMIT
    ) -> TradingResult:
        """
        Place buy order

        Args:
            code: Stock code
            price: Order price
            quantity: Order quantity
            order_type: Order type (LIMIT or MARKET)

        Returns:
            TradingResult
        """
        logger.info(f"Placing buy order: {code} {quantity} shares @ {price}")

        if not self.window:
            return TradingResult(False, "buy", "Not connected to window")

        try:
            # Input stock code
            result = self.input_stock_code(code)
            if not result.success:
                return result

            # Input price
            result = self.input_price(price)
            if not result.success:
                return result

            # Input quantity
            result = self.input_quantity(quantity)
            if not result.success:
                return result

            # Click buy button
            result = self.click_buy_button()
            if not result.success:
                return result

            # Take screenshot for verification
            try:
                screenshot = screenshot_window(self.window)
                screenshot_path = self.screenshot_manager.save_log_screenshot(
                    screenshot,
                    "buy_order",
                    {
                        "action": "buy",
                        "code": code,
                        "price": price,
                        "quantity": quantity,
                        "order_type": order_type.value
                    }
                )
            except Exception as e:
                logger.error(f"Failed to save screenshot: {e}")
                screenshot_path = None

            logger.info(f"Buy order placed successfully: {code}")
            return TradingResult(
                True,
                "buy",
                f"Buy order placed: {code} {quantity} shares @ {price}",
                screenshot_path,
                {
                    "code": code,
                    "price": price,
                    "quantity": quantity,
                    "order_type": order_type.value
                }
            )

        except Exception as e:
            logger.error(f"Error placing buy order: {e}")
            return TradingResult(
                False,
                "buy",
                f"Error: {str(e)}"
            )

    def sell(
        self,
        code: str,
        price: float,
        quantity: int,
        order_type: OrderType = OrderType.LIMIT
    ) -> TradingResult:
        """
        Place sell order

        Args:
            code: Stock code
            price: Order price
            quantity: Order quantity
            order_type: Order type (LIMIT or MARKET)

        Returns:
            TradingResult
        """
        logger.info(f"Placing sell order: {code} {quantity} shares @ {price}")

        if not self.window:
            return TradingResult(False, "sell", "Not connected to window")

        try:
            # Input stock code
            result = self.input_stock_code(code)
            if not result.success:
                return result

            # Input price
            result = self.input_price(price)
            if not result.success:
                return result

            # Input quantity
            result = self.input_quantity(quantity)
            if not result.success:
                return result

            # Click sell button
            result = self.click_sell_button()
            if not result.success:
                return result

            # Take screenshot for verification
            try:
                screenshot = screenshot_window(self.window)
                screenshot_path = self.screenshot_manager.save_log_screenshot(
                    screenshot,
                    "sell_order",
                    {
                        "action": "sell",
                        "code": code,
                        "price": price,
                        "quantity": quantity,
                        "order_type": order_type.value
                    }
                )
            except Exception as e:
                logger.error(f"Failed to save screenshot: {e}")
                screenshot_path = None

            logger.info(f"Sell order placed successfully: {code}")
            return TradingResult(
                True,
                "sell",
                f"Sell order placed: {code} {quantity} shares @ {price}",
                screenshot_path,
                {
                    "code": code,
                    "price": price,
                    "quantity": quantity,
                    "order_type": order_type.value
                }
            )

        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return TradingResult(
                False,
                "sell",
                f"Error: {str(e)}"
            )

    def cancel_order(self, order_id: Optional[str] = None) -> TradingResult:
        """
        Cancel order

        Args:
            order_id: Optional order ID to cancel (if None, cancels first pending order)

        Returns:
            TradingResult
        """
        logger.info(f"Cancelling order: {order_id if order_id else 'first pending'}")

        if not self.window:
            return TradingResult(False, "cancel", "Not connected to window")

        try:
            # Click cancel button
            result = self.click_cancel_button()
            if not result.success:
                return result

            # Take screenshot for verification
            try:
                screenshot = screenshot_window(self.window)
                screenshot_path = self.screenshot_manager.save_log_screenshot(
                    screenshot,
                    "cancel_order",
                    {"action": "cancel", "order_id": order_id}
                )
            except Exception as e:
                logger.error(f"Failed to save screenshot: {e}")
                screenshot_path = None

            logger.info("Order cancelled successfully")
            return TradingResult(
                True,
                "cancel",
                f"Order cancelled: {order_id if order_id else 'first pending'}",
                screenshot_path,
                {"order_id": order_id}
            )

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return TradingResult(
                False,
                "cancel",
                f"Error: {str(e)}"
            )


# Global trader instance
trader = THSTrader()
