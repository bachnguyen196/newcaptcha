"""Computer-vision solver for the local slider CAPTCHA demonstration."""

import base64
import binascii
import io

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 1_000_000
EXPECTED_CANVAS_SIZE = (320, 160)
EXPECTED_PIECE_SIZE = (48, 48)


def _decode_data_uri(data_uri, expected_size, image_name, mode):
    if not isinstance(data_uri, str) or not data_uri.startswith('data:image/'):
        raise ValueError(f'{image_name} must be an image data URI.')

    try:
        header, encoded = data_uri.split(',', 1)
        if ';base64' not in header:
            raise ValueError(f'{image_name} must be base64-encoded.')
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError(f'{image_name} exceeds the size limit.')
        with Image.open(io.BytesIO(raw)) as image:
            if image.size != expected_size:
                raise ValueError(
                    f'{image_name} must be {expected_size[0]}x{expected_size[1]} pixels.'
                )
            image.load()
            decoded = image.convert(mode)
    except (ValueError, binascii.Error, UnicodeError, UnidentifiedImageError, OSError) as error:
        raise ValueError(f'{image_name} is not a valid supported image.') from error
    return np.asarray(decoded)


def solve_slider_images(canvas_data_uri, piece_data_uri, target_y):
    """Find a jigsaw slot using only the rendered canvas and transparent piece."""
    if isinstance(target_y, bool) or not isinstance(target_y, int):
        raise ValueError('The public puzzle row must be an integer.')
    if not 0 <= target_y <= EXPECTED_CANVAS_SIZE[1] - EXPECTED_PIECE_SIZE[1]:
        raise ValueError('The public puzzle row is outside the canvas.')

    canvas_rgb = _decode_data_uri(
        canvas_data_uri, EXPECTED_CANVAS_SIZE, 'Canvas image', 'RGB'
    )
    piece_rgba = _decode_data_uri(
        piece_data_uri, EXPECTED_PIECE_SIZE, 'Puzzle piece', 'RGBA'
    )

    piece_alpha = piece_rgba[:, :, 3]

    canvas_hsv = cv2.cvtColor(canvas_rgb, cv2.COLOR_RGB2HSV)
    slot_outline = cv2.inRange(
        canvas_hsv,
        np.array([75, 70, 60], dtype=np.uint8),
        np.array([115, 255, 255], dtype=np.uint8)
    )
    piece_edges = cv2.Canny(piece_alpha, 80, 160)
    if cv2.countNonZero(piece_edges) == 0:
        raise ValueError('Puzzle piece has no detectable shape boundary.')

    # The challenge API exposes the row, so only the horizontal position must be inferred.
    search_top = max(0, target_y - 2)
    search_bottom = min(
        EXPECTED_CANVAS_SIZE[1],
        target_y + EXPECTED_PIECE_SIZE[1] + 2
    )
    search_area = slot_outline[search_top:search_bottom, :]
    scores = cv2.matchTemplate(search_area, piece_edges, cv2.TM_CCORR_NORMED)

    # The loose piece begins at the left edge; the target is generated farther right.
    minimum_x = EXPECTED_PIECE_SIZE[0] + 8
    scores[:, :minimum_x] = -1
    _, best_score, _, best_location = cv2.minMaxLoc(scores)
    if best_score < 0.15:
        raise ValueError('No reliable jigsaw slot match was found.')

    second_best = scores.copy()
    x, y = best_location
    exclusion = 8
    second_best[
        max(0, y - exclusion):min(second_best.shape[0], y + exclusion + 1),
        max(minimum_x, x - exclusion):min(second_best.shape[1], x + exclusion + 1)
    ] = -1
    second_score = float(cv2.minMaxLoc(second_best)[1])

    return {
        'x': int(x),
        'y': search_top + int(y),
        'score': round(float(best_score), 4),
        'second_score': round(second_score, 4)
    }
