import numpy as np
from PIL import Image

from app.preprocess import PreprocessOptions, pick_threshold, preprocess, threshold_candidates, to_gray, upscale


def test_small_images_are_upscaled_to_min_height():
    gray = np.full((200, 100), 128, dtype=np.uint8)

    scaled = upscale(gray, 1000)

    assert scaled.shape == (1000, 500)


def test_large_images_are_left_alone():
    gray = np.full((1200, 600), 128, dtype=np.uint8)

    assert upscale(gray, 1000) is gray


def test_preprocess_returns_binary_uint8(receipt_image):
    binary = preprocess(receipt_image)

    assert binary.dtype == np.uint8
    assert binary.shape[0] >= 1000
    assert set(np.unique(binary)).issubset({0, 255})


def test_text_pixels_survive_preprocessing(receipt_image):
    binary = preprocess(receipt_image)

    dark_ratio = (binary == 0).mean()
    assert 0.005 < dark_ratio < 0.5


def test_threshold_pick_prefers_brightest_candidate():
    enhanced = to_gray(Image.new("RGB", (64, 64), (240, 240, 240)))
    candidates = threshold_candidates(enhanced, PreprocessOptions())

    name, image = pick_threshold(candidates)

    assert name in candidates
    assert image.shape == enhanced.shape
