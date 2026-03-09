"""
截图功能模块
Screenshot Module for UI Element Capture
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Tuple, Optional, List
from datetime import datetime

from config.settings import settings
from utils.logger import logger


class ScreenshotManager:
    """
    Screenshot manager for capturing and managing screenshots
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize screenshot manager

        Args:
            base_dir: Base directory for saving screenshots
        """
        if base_dir is None:
            base_dir = settings.SCREENSHOT_PATH
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.templates_dir = self.base_dir / "templates"
        self.tests_dir = self.base_dir / "tests"
        self.logs_dir = self.base_dir / "logs"

        for dir_path in [self.templates_dir, self.tests_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)

    def save_template(
        self,
        image: np.ndarray,
        name: str,
        description: str = ""
    ) -> Path:
        """
        Save template image

        Args:
            image: Image array (BGR format)
            name: Template name
            description: Optional description

        Returns:
            Path to saved template
        """
        filename = f"{name}.png"
        filepath = self.templates_dir / filename

        cv2.imwrite(str(filepath), image)

        # Save description
        if description:
            desc_file = self.templates_dir / f"{name}.txt"
            with open(desc_file, 'w', encoding='utf-8') as f:
                f.write(description)

        logger.info(f"Template saved: {filepath}")
        return filepath

    def load_template(self, name: str) -> Optional[np.ndarray]:
        """
        Load template image

        Args:
            name: Template name

        Returns:
            Template image or None if not found
        """
        filepath = self.templates_dir / f"{name}.png"
        if not filepath.exists():
            logger.warning(f"Template not found: {filepath}")
            return None

        image = cv2.imread(str(filepath), cv2.IMREAD_COLOR)
        if image is None:
            logger.error(f"Failed to load template: {filepath}")
            return None

        logger.debug(f"Template loaded: {name}")
        return image

    def list_templates(self) -> List[str]:
        """Get list of available templates"""
        templates = []
        for filepath in self.templates_dir.glob("*.png"):
            templates.append(filepath.stem)
        return sorted(templates)

    def save_test_screenshot(
        self,
        image: np.ndarray,
        name: Optional[str] = None
    ) -> Path:
        """
        Save test screenshot

        Args:
            image: Image array (BGR format)
            name: Optional name (uses timestamp if not provided)

        Returns:
            Path to saved screenshot
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"test_{timestamp}"

        filename = f"{name}.png"
        filepath = self.tests_dir / filename

        cv2.imwrite(str(filepath), image)
        logger.info(f"Test screenshot saved: {filepath}")
        return filepath

    def save_log_screenshot(
        self,
        image: np.ndarray,
        action: str,
        metadata: dict = None
    ) -> Path:
        """
        Save screenshot with action log

        Args:
            image: Image array (BGR format)
            action: Action description
            metadata: Optional metadata dictionary

        Returns:
            Path to saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{action}_{timestamp}.png"
        filepath = self.logs_dir / filename

        cv2.imwrite(str(filepath), image)

        # Save metadata
        if metadata:
            import json
            meta_file = self.logs_dir / f"{action}_{timestamp}.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Log screenshot saved: {filepath}")
        return filepath

    def crop_region(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        Crop region from image

        Args:
            image: Source image
            region: (x, y, width, height) region to crop

        Returns:
            Cropped image
        """
        x, y, width, height = region
        cropped = image[y:y+height, x:x+width]
        logger.debug(f"Cropped region: {region}, result shape: {cropped.shape}")
        return cropped

    def draw_rectangle(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        label: Optional[str] = None
    ) -> np.ndarray:
        """
        Draw rectangle on image (returns copy)

        Args:
            image: Source image
            region: (x, y, width, height) region
            color: BGR color tuple
            thickness: Line thickness
            label: Optional label text

        Returns:
            Image with rectangle drawn
        """
        result = image.copy()
        x, y, width, height = region
        pt1 = (x, y)
        pt2 = (x + width, y + height)

        cv2.rectangle(result, pt1, pt2, color, thickness)

        if label:
            # Add text label
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            text_thickness = 2
            text_size = cv2.getTextSize(label, font, font_scale, text_thickness)[0]

            # Draw background for text
            text_bg_pt1 = (x, y - text_size[1] - 10)
            text_bg_pt2 = (x + text_size[0] + 10, y)
            cv2.rectangle(result, text_bg_pt1, text_bg_pt2, color, -1)

            # Draw text
            text_pt = (x + 5, y - 5)
            cv2.putText(result, label, text_pt, font, font_scale, (255, 255, 255), text_thickness)

        return result

    def draw_matches(
        self,
        image: np.ndarray,
        matches: List[Tuple[int, int, int, int]],
        labels: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Draw multiple matches on image

        Args:
            image: Source image
            matches: List of (x, y, width, height) regions
            labels: Optional labels for each match

        Returns:
            Image with rectangles drawn
        """
        result = image.copy()

        colors = [
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]

        for i, match in enumerate(matches):
            color = colors[i % len(colors)]
            label = labels[i] if labels and i < len(labels) else f"Match {i+1}"
            result = self.draw_rectangle(result, match, color, 2, label)

        return result

    def extract_text_region(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int]
    ) -> str:
        """
        Extract text from image region (placeholder for OCR)

        Args:
            image: Source image
            region: (x, y, width, height) region containing text

        Returns:
            Extracted text string
        """
        # This is a placeholder - implement OCR if needed
        # For now, returns region info
        x, y, width, height = region
        return f"Region at ({x}, {y}), size: {width}x{height}"


# Global instance
screenshot_manager = ScreenshotManager()


if __name__ == "__main__":
    # Test screenshot manager
    print("Screenshot Manager Test")
    print(f"Base directory: {screenshot_manager.base_dir}")
    print(f"Templates directory: {screenshot_manager.templates_dir}")
    print(f"Available templates: {screenshot_manager.list_templates()}")
