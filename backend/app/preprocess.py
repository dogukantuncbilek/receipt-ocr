from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class PreprocessOptions:
    min_height: int = 1000
    bilateral_diameter: int = 11
    bilateral_sigma: int = 17
    clahe_clip_limit: float = 3.0
    clahe_tile: int = 8
    adaptive_block_size: int = 15
    adaptive_c: int = 10


DEFAULT_OPTIONS = PreprocessOptions()


def to_gray(image: Image.Image) -> np.ndarray:
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


def upscale(gray: np.ndarray, min_height: int) -> np.ndarray:
    height, width = gray.shape[:2]
    if height >= min_height:
        return gray
    scale = min_height / height
    return cv2.resize(gray, (int(width * scale), min_height), interpolation=cv2.INTER_CUBIC)


def denoise_and_enhance(gray: np.ndarray, options: PreprocessOptions) -> np.ndarray:
    bilateral = cv2.bilateralFilter(gray, options.bilateral_diameter, options.bilateral_sigma, options.bilateral_sigma)
    blurred = cv2.GaussianBlur(bilateral, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=options.clahe_clip_limit, tileGridSize=(options.clahe_tile, options.clahe_tile))
    return clahe.apply(blurred)


def threshold_candidates(enhanced: np.ndarray, options: PreprocessOptions) -> dict[str, np.ndarray]:
    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mean = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, options.adaptive_block_size, options.adaptive_c
    )
    gaussian = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, options.adaptive_block_size, options.adaptive_c
    )
    return {"otsu": otsu, "adaptive_mean": mean, "adaptive_gaussian": gaussian}


def pick_threshold(candidates: dict[str, np.ndarray]) -> tuple[str, np.ndarray]:
    name, image = max(candidates.items(), key=lambda item: cv2.countNonZero(item[1]))
    return name, image


def preprocess(image: Image.Image, options: PreprocessOptions = DEFAULT_OPTIONS) -> np.ndarray:
    gray = upscale(to_gray(image), options.min_height)
    enhanced = denoise_and_enhance(gray, options)
    _, binary = pick_threshold(threshold_candidates(enhanced, options))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)


def to_pil(binary: np.ndarray) -> Image.Image:
    return Image.fromarray(binary)
