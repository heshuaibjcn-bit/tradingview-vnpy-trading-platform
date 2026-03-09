"""
同花顺窗口识别模块
Window Recognition Module for Tonghuashun (同花顺) Trading Client
"""

import sys
import platform
from typing import Optional, Tuple, List
from pathlib import Path
import numpy as np
from PIL import ImageGrab
import cv2
import pyautogui

from config.settings import settings
from utils.logger import logger

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Windows API imports (only on Windows)
if IS_WINDOWS:
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    user32.EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.POINTER(ctypes.wintypes.HWND), ctypes.POINTER(ctypes.wintypes.LPARAM))

    HWND = ctypes.wintypes.HWND
    LPARAM = ctypes.wintypes.LPARAM
    WPARAM = ctypes.wintypes.WPARAM
    DWORD = ctypes.wintypes.DWORD
    LONG = ctypes.wintypes.LONG

    # Constants
    WM_COMMAND = 0x0111
    WM_CLOSE = 0x0010
else:
    # On non-Windows platforms, use placeholder types
    HWND = int
    user32 = None


if IS_WINDOWS:
    class Rect(ctypes.Structure):
        """Windows RECT structure"""
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

        @property
        def width(self) -> int:
            return self.right - self.left

        @property
        def height(self) -> int:
            return self.bottom - self.top

        @property
        def tuple(self) -> Tuple[int, int, int, int]:
            return (self.left, self.top, self.right, self.bottom)
else:
    class Rect:
        """Simple Rect class for non-Windows platforms"""
        def __init__(self, left=0, top=0, right=0, bottom=0):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom

        @property
        def width(self) -> int:
            return self.right - self.left

        @property
        def height(self) -> int:
            return self.bottom - self.top

        @property
        def tuple(self) -> Tuple[int, int, int, int]:
            return (self.left, self.top, self.right, self.bottom)


class WindowInfo:
    """Window information container"""

    def __init__(self, hwnd: int, title: str, rect: Rect):
        self.hwnd = hwnd
        self.title = title
        self.rect = rect

    def __repr__(self) -> str:
        return f"WindowInfo(hwnd={self.hwnd}, title='{self.title}', rect={self.rect.tuple})"


def get_window_text(hwnd: HWND) -> str:
    """Get window title text"""
    length = user32.GetWindowTextLengthW(hwnd) + 1
    buffer = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buffer, length)
    return buffer.value


def get_window_rect(hwnd: HWND) -> Optional[Rect]:
    """Get window rectangle"""
    rect = Rect()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return rect
    return None


def enum_windows_callback(hwnd: HWND, lParam: LPARAM) -> bool:
    """Callback for enumerating windows (Windows only)"""
    if user32.IsWindowVisible(hwnd):
        title = get_window_text(hwnd)
        if title:
            rect = get_window_rect(hwnd)
            if rect:
                window_info = WindowInfo(hwnd, title, rect)
                # Store in global list (hacky but works for callback)
                enum_windows_callback.windows.append(window_info)
    return True


enum_windows_callback.windows = []  # type: ignore


def find_all_windows() -> List[WindowInfo]:
    """Find all visible windows (Windows only)"""
    if not IS_WINDOWS:
        logger.warning("Window enumeration is only supported on Windows")
        return []

    enum_windows_callback.windows = []
    user32.EnumWindows(user32.EnumWindowsProc(enum_windows_callback), 0)
    return enum_windows_callback.windows


def find_tonghuashun_window() -> Optional[WindowInfo]:
    """
    Find Tonghuashun (同花顺) trading client window

    Returns:
        WindowInfo if found, None otherwise
    Note: Only works on Windows. On other platforms, returns None.
    """
    if not IS_WINDOWS:
        logger.warning("Tonghuashun window finding is only supported on Windows")
        logger.info("On non-Windows platforms, use screenshot_region() instead")
        return None

    windows = find_all_windows()

    # Keywords to identify Tonghuashun window
    keywords = ['同花顺', 'Tonghuashun', 'THS', '同花顺软件']

    for window in windows:
        title_lower = window.title.lower()
        for keyword in keywords:
            if keyword.lower() in title_lower:
                logger.info(f"Found Tonghuashun window: {window.title}")
                return window

    logger.warning("Tonghuashun window not found")
    return None


def bring_window_to_front(hwnd: HWND) -> bool:
    """
    Bring window to front (Windows only)

    Args:
        hwnd: Window handle

    Returns:
        True if successful, False otherwise
    """
    if not IS_WINDOWS:
        logger.warning("Window management is only supported on Windows")
        return False

    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

        user32.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        logger.error(f"Failed to bring window to front: {e}")
        return False


def is_window_minimized(hwnd: HWND) -> bool:
    """Check if window is minimized (Windows only)"""
    if not IS_WINDOWS:
        return False
    return user32.IsIconic(hwnd) != 0


def screenshot_window(window_info: WindowInfo) -> np.ndarray:
    """
    Take screenshot of a window

    Args:
        window_info: Window information

    Returns:
        Screenshot as numpy array (BGR format for OpenCV)
    """
    rect = window_info.rect

    # Capture screenshot using PIL
    screenshot = ImageGrab.grab(bbox=rect.tuple)

    # Convert to numpy array and BGR format
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    logger.debug(f"Screenshot taken: {screenshot_bgr.shape}")
    return screenshot_bgr


def screenshot_region(region: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Take screenshot of a screen region (cross-platform)

    Args:
        region: (x, y, width, height) region to capture

    Returns:
        Screenshot as numpy array (BGR format for OpenCV)
    """
    x, y, width, height = region
    bbox = (x, y, x + width, y + height)

    # Capture screenshot using PIL
    screenshot = ImageGrab.grab(bbox=bbox)

    # Convert to numpy array and BGR format
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    logger.debug(f"Screenshot taken: {screenshot_bgr.shape}")
    return screenshot_bgr


def screenshot_screen() -> np.ndarray:
    """
    Take screenshot of entire screen (cross-platform)

    Returns:
        Screenshot as numpy array (BGR format for OpenCV)
    """
    # Capture screenshot using PIL
    screenshot = ImageGrab.grab()

    # Convert to numpy array and BGR format
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    logger.debug(f"Screenshot taken: {screenshot_bgr.shape}")
    return screenshot_bgr


def save_screenshot(image: np.ndarray, filename: str) -> None:
    """
    Save screenshot to file

    Args:
        image: Image array (BGR format)
        filename: Output filename
    """
    cv2.imwrite(filename, image)
    logger.info(f"Screenshot saved to {filename}")


class TemplateMatcher:
    """
    Template matching for UI element detection

    Uses OpenCV template matching to locate UI elements in screenshots
    """

    def __init__(self, template_dir: str = None):
        """
        Initialize template matcher

        Args:
            template_dir: Directory containing template images
        """
        if template_dir is None:
            template_dir = Path(settings.SCREENSHOT_PATH) / "templates"
        else:
            template_dir = Path(template_dir)
        self.template_dir = template_dir
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, template_name: str) -> Optional[np.ndarray]:
        """
        Load template image

        Args:
            template_name: Template filename

        Returns:
            Template image as numpy array, or None if not found
        """
        template_path = self.template_dir / template_name
        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}")
            return None

        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            logger.error(f"Failed to load template: {template_path}")
            return None

        logger.debug(f"Template loaded: {template_name}, shape: {template.shape}")
        return template

    def find_template(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: float = 0.8,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Find template in screenshot

        Args:
            screenshot: Screenshot image (BGR format)
            template_name: Template filename
            threshold: Confidence threshold (0-1)
            method: OpenCV template matching method

        Returns:
            (x, y, width, height) of best match, or None if below threshold
        """
        template = self.load_template(template_name)
        if template is None:
            return None

        # Get template dimensions
        template_height, template_width = template.shape[:2]

        # Check if screenshot is smaller than template
        if screenshot.shape[0] < template_height or screenshot.shape[1] < template_width:
            logger.warning("Screenshot is smaller than template")
            return None

        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, method)

        # Find best match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # For TM_SQDIFF methods, minimum is best match
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
            confidence = 1 - min_val
        else:
            top_left = max_loc
            confidence = max_val

        logger.debug(f"Template matching confidence: {confidence:.3f}")

        if confidence >= threshold:
            bottom_right = (
                top_left[0] + template_width,
                top_left[1] + template_height
            )
            return (*top_left, template_width, template_height)

        logger.warning(f"Template match below threshold: {confidence:.3f} < {threshold}")
        return None

    def find_all_templates(
        self,
        screenshot: np.ndarray,
        template_name: str,
        threshold: float = 0.8,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> List[Tuple[int, int, int, int]]:
        """
        Find all instances of template in screenshot

        Args:
            screenshot: Screenshot image (BGR format)
            template_name: Template filename
            threshold: Confidence threshold (0-1)
            method: OpenCV template matching method

        Returns:
            List of (x, y, width, height) tuples
        """
        template = self.load_template(template_name)
        if template is None:
            return []

        template_height, template_width = template.shape[:2]

        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, method)

        # Find all locations above threshold
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            locations = np.where(result <= (1 - threshold))
        else:
            locations = np.where(result >= threshold)

        matches = []
        for pt in zip(*locations[::-1]):  # Switch x and y columns
            matches.append((pt[0], pt[1], template_width, template_height))

        logger.debug(f"Found {len(matches)} template matches")
        return matches

    def create_template_from_screenshot(
        self,
        screenshot: np.ndarray,
        region: Tuple[int, int, int, int],
        template_name: str
    ) -> None:
        """
        Create template from screenshot region

        Args:
            screenshot: Screenshot image (BGR format)
            region: (x, y, width, height) region to extract
            template_name: Output template filename
        """
        x, y, width, height = region
        template = screenshot[y:y+height, x:x+width]
        template_path = self.template_dir / template_name
        cv2.imwrite(str(template_path), template)
        logger.info(f"Template saved: {template_path}")


class CoordinateManager:
    """
    Coordinate manager for UI element positions

    Saves and loads element coordinates from configuration
    """

    def __init__(self, config_file: str = None):
        """
        Initialize coordinate manager

        Args:
            config_file: Path to configuration file
        """
        if config_file is None:
            config_file = Path(settings.SCREENSHOT_PATH) / "coordinates.json"
        else:
            config_file = Path(config_file)
        self.config_file = config_file
        self.coordinates = self._load_coordinates()

    def _load_coordinates(self) -> dict:
        """Load coordinates from file"""
        if self.config_file.exists():
            import json
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_coordinates(self) -> None:
        """Save coordinates to file"""
        import json
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.coordinates, f, indent=2, ensure_ascii=False)
        logger.info(f"Coordinates saved to {self.config_file}")

    def set_coordinate(self, name: str, region: Tuple[int, int, int, int]) -> None:
        """
        Set coordinate for an element

        Args:
            name: Element name
            region: (x, y, width, height) region
        """
        self.coordinates[name] = {
            'x': region[0],
            'y': region[1],
            'width': region[2],
            'height': region[3]
        }
        self._save_coordinates()

    def get_coordinate(self, name: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Get coordinate for an element

        Args:
            name: Element name

        Returns:
            (x, y, width, height) or None if not found
        """
        coord = self.coordinates.get(name)
        if coord:
            return (coord['x'], coord['y'], coord['width'], coord['height'])
        return None

    def list_coordinates(self) -> List[str]:
        """Get list of all coordinate names"""
        return list(self.coordinates.keys())

    def delete_coordinate(self, name: str) -> None:
        """Delete coordinate"""
        if name in self.coordinates:
            del self.coordinates[name]
            self._save_coordinates()


# Global instances
matcher = TemplateMatcher()
coord_manager = CoordinateManager()


if __name__ == "__main__":
    # Test window detection
    logger.info("Searching for Tonghuashun window...")
    window = find_tonghuashun_window()

    if window:
        print(f"Found window: {window}")
        print(f"Title: {window.title}")
        print(f"Position: ({window.rect.left}, {window.rect.top})")
        print(f"Size: {window.rect.width}x{window.rect.height}")

        # Bring to front
        bring_window_to_front(window.hwnd)

        # Take screenshot
        screenshot = screenshot_window(window)
        save_screenshot(screenshot, "test_screenshot.png")
    else:
        print("Tonghuashun window not found. Please make sure it's running.")
