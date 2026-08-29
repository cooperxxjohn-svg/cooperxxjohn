"""
Smart Image Processor
Handles image quality assessment, enhancement, and preprocessing for optimal extraction
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from dataclasses import dataclass
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality assessment results for an image"""
    overall_score: float  # 0-1, where 1 is perfect
    rotation_angle: float  # Detected rotation in degrees
    blur_score: float  # 0-1, lower is blurrier
    contrast_score: float  # 0-1
    resolution: Tuple[int, int]  # (width, height)
    needs_enhancement: bool
    needs_upscale: bool
    is_searchable_text: bool  # If it's already text-based


class SmartImageProcessor:
    """
    Intelligent image processing for construction documents
    Handles quality assessment, auto-enhancement, and optimization
    """

    def __init__(self):
        self.min_resolution = (1000, 1000)
        self.target_dpi = 300
        self.blur_threshold = 100.0
        self.contrast_threshold = 50.0

    def assess_quality(self, image_path: str) -> QualityScore:
        """
        Assess image quality and determine what processing is needed

        Args:
            image_path: Path to image file

        Returns:
            QualityScore with assessment results
        """
        try:
            # Load image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")

            # Convert to grayscale for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 1. Check resolution
            height, width = img.shape[:2]
            resolution = (width, height)
            needs_upscale = width < self.min_resolution[0] or height < self.min_resolution[1]

            # 2. Detect blur
            blur_score = self._detect_blur(gray)

            # 3. Assess contrast
            contrast_score = self._assess_contrast(gray)

            # 4. Detect rotation
            rotation_angle = self._detect_rotation(gray)

            # 5. Calculate overall quality score
            overall_score = self._calculate_overall_score(
                blur_score, contrast_score, resolution, rotation_angle
            )

            # 6. Determine if enhancement is needed
            needs_enhancement = (
                blur_score < 0.7 or
                contrast_score < 0.6 or
                abs(rotation_angle) > 1.0
            )

            # 7. Check if it's already searchable text (high contrast, sharp)
            is_searchable_text = blur_score > 0.85 and contrast_score > 0.75

            logger.info(f"Quality Assessment: overall={overall_score:.2f}, blur={blur_score:.2f}, "
                       f"contrast={contrast_score:.2f}, rotation={rotation_angle:.2f}°")

            return QualityScore(
                overall_score=overall_score,
                rotation_angle=rotation_angle,
                blur_score=blur_score,
                contrast_score=contrast_score,
                resolution=resolution,
                needs_enhancement=needs_enhancement,
                needs_upscale=needs_upscale,
                is_searchable_text=is_searchable_text
            )

        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            # Return default low-quality score
            return QualityScore(
                overall_score=0.5,
                rotation_angle=0.0,
                blur_score=0.5,
                contrast_score=0.5,
                resolution=(0, 0),
                needs_enhancement=True,
                needs_upscale=False,
                is_searchable_text=False
            )

    def _detect_blur(self, gray_image: np.ndarray) -> float:
        """
        Detect image blur using Laplacian variance method
        Returns score from 0-1, where 1 is sharp
        """
        laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()

        # Normalize to 0-1 range
        # Construction docs typically have variance > 100 for sharp images
        normalized_score = min(laplacian_var / self.blur_threshold, 1.0)

        return normalized_score

    def _assess_contrast(self, gray_image: np.ndarray) -> float:
        """
        Assess image contrast using standard deviation
        Returns score from 0-1, where 1 is good contrast
        """
        std_dev = np.std(gray_image)

        # Normalize to 0-1 range
        # Good construction docs have std dev > 50
        normalized_score = min(std_dev / self.contrast_threshold, 1.0)

        return normalized_score

    def _detect_rotation(self, gray_image: np.ndarray) -> float:
        """
        Detect rotation angle using Hough Line Transform
        Returns angle in degrees (-45 to +45)
        """
        try:
            # Edge detection
            edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)

            # Detect lines
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is None:
                return 0.0

            # Calculate angles of detected lines
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)

            if not angles:
                return 0.0

            # Use median angle
            median_angle = np.median(angles)

            # Only report significant rotation (> 0.5 degrees)
            if abs(median_angle) < 0.5:
                return 0.0

            return median_angle

        except Exception as e:
            logger.warning(f"Could not detect rotation: {e}")
            return 0.0

    def _calculate_overall_score(
        self,
        blur_score: float,
        contrast_score: float,
        resolution: Tuple[int, int],
        rotation_angle: float
    ) -> float:
        """Calculate weighted overall quality score"""

        # Resolution score (0-1)
        width, height = resolution
        min_dim = min(width, height)
        resolution_score = min(min_dim / self.min_resolution[0], 1.0)

        # Rotation penalty
        rotation_penalty = max(0, 1.0 - abs(rotation_angle) / 10.0)

        # Weighted average
        overall = (
            blur_score * 0.35 +
            contrast_score * 0.30 +
            resolution_score * 0.20 +
            rotation_penalty * 0.15
        )

        return overall

    def auto_enhance(self, image_path: str, output_path: str, quality_score: QualityScore) -> str:
        """
        Automatically enhance image based on quality assessment

        Args:
            image_path: Input image path
            output_path: Output image path
            quality_score: QualityScore from assess_quality()

        Returns:
            Path to enhanced image
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                logger.warning(f"Could not load image for enhancement: {image_path}")
                return image_path

            # 1. Rotate if needed
            if abs(quality_score.rotation_angle) > 0.5:
                img = self._rotate_image(img, -quality_score.rotation_angle)
                logger.info(f"Rotated image by {-quality_score.rotation_angle:.2f}°")

            # 2. Enhance contrast if needed
            if quality_score.contrast_score < 0.6:
                img = self._enhance_contrast(img)
                logger.info("Enhanced image contrast")

            # 3. Reduce noise/sharpen if blurry
            if quality_score.blur_score < 0.7:
                img = self._sharpen_image(img)
                logger.info("Sharpened blurry image")

            # 4. Upscale if resolution is too low
            if quality_score.needs_upscale:
                img = self._upscale_image(img)
                logger.info(f"Upscaled image to {img.shape[1]}x{img.shape[0]}")

            # Save enhanced image
            cv2.imwrite(output_path, img)
            logger.info(f"Saved enhanced image to {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image_path  # Return original if enhancement fails

    def _rotate_image(self, img: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle"""
        height, width = img.shape[:2]
        center = (width // 2, height // 2)

        # Get rotation matrix
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new dimensions
        cos = np.abs(matrix[0, 0])
        sin = np.abs(matrix[0, 1])
        new_width = int((height * sin) + (width * cos))
        new_height = int((height * cos) + (width * sin))

        # Adjust translation
        matrix[0, 2] += (new_width / 2) - center[0]
        matrix[1, 2] += (new_height / 2) - center[1]

        # Rotate
        rotated = cv2.warpAffine(img, matrix, (new_width, new_height),
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(255, 255, 255))

        return rotated

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # Merge and convert back
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return enhanced

    def _sharpen_image(self, img: np.ndarray) -> np.ndarray:
        """Sharpen blurry image"""
        # Unsharp mask technique
        gaussian = cv2.GaussianBlur(img, (0, 0), 2.0)
        sharpened = cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)

        return sharpened

    def _upscale_image(self, img: np.ndarray) -> np.ndarray:
        """Upscale low-resolution image"""
        height, width = img.shape[:2]

        # Calculate scale factor to reach minimum resolution
        scale_x = self.min_resolution[0] / width
        scale_y = self.min_resolution[1] / height
        scale = max(scale_x, scale_y, 1.5)  # At least 1.5x

        new_width = int(width * scale)
        new_height = int(height * scale)

        # Use INTER_CUBIC for upscaling (better quality)
        upscaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

        return upscaled

    def prepare_for_ocr(self, image_path: str) -> str:
        """
        Prepare image specifically for OCR processing
        Applies aggressive preprocessing for best OCR results

        Args:
            image_path: Path to input image

        Returns:
            Path to OCR-ready image
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 1. Denoise
            gray = cv2.fastNlMeansDenoising(gray, h=10)

            # 2. Binarization (Otsu's method)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 3. Morphological operations to remove noise
            kernel = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Save OCR-ready image
            ocr_path = image_path.replace('.', '_ocr.')
            cv2.imwrite(ocr_path, binary)

            logger.info(f"Prepared image for OCR: {ocr_path}")
            return ocr_path

        except Exception as e:
            logger.error(f"Error preparing image for OCR: {e}")
            return image_path


# Convenience function
def process_image(image_path: str, output_dir: str = None) -> Tuple[str, QualityScore]:
    """
    Process a single image: assess quality and enhance if needed

    Args:
        image_path: Path to input image
        output_dir: Directory for output (optional)

    Returns:
        Tuple of (enhanced_image_path, quality_score)
    """
    processor = SmartImageProcessor()

    # Assess quality
    quality = processor.assess_quality(image_path)

    # Enhance if needed
    if quality.needs_enhancement:
        if output_dir:
            import os
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, f"enhanced_{filename}")
        else:
            output_path = image_path.replace('.', '_enhanced.')

        enhanced_path = processor.auto_enhance(image_path, output_path, quality)
        return enhanced_path, quality
    else:
        return image_path, quality
