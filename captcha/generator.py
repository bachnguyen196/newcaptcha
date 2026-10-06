import io
import os
import uuid
import base64
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# Preset color themes for procedural generation
PALETTES = [
    # Cyber Tech (Cyan, Blue, Indigo)
    [(14, 165, 233), (99, 102, 241), (15, 23, 42), (56, 189, 248)],
    # Midnight Neon (Purple, Violet, Deep Slate)
    [(168, 85, 247), (236, 72, 153), (30, 27, 75), (217, 70, 239)],
    # Emerald Matrix (Emerald, Mint, Dark Teal)
    [(16, 185, 129), (20, 184, 166), (6, 78, 59), (52, 211, 153)],
    # Sunset Crimson (Amber, Rose, Dark Slate)
    [(245, 158, 11), (244, 63, 94), (67, 20, 7), (251, 146, 60)],
    # Deep Ocean (Navy, Cyan, Cobalt)
    [(37, 99, 235), (6, 182, 212), (10, 25, 47), (96, 165, 250)]
]

def generate_procedural_background(width=320, height=160):
    """
    Generate an aesthetic procedural background with smooth gradients,
    abstract geometry, and glowing accents.
    """
    palette = random.choice(PALETTES)
    c_primary, c_secondary, c_dark, c_accent = palette

    # Create base image with smooth vertical linear gradient
    base = Image.new('RGB', (width, height), c_dark)
    draw = ImageDraw.Draw(base)

    for y in range(height):
        ratio = y / float(height)
        r = int(c_dark[0] * (1 - ratio) + c_secondary[0] * ratio * 0.4 + c_primary[0] * ratio * 0.6)
        g = int(c_dark[1] * (1 - ratio) + c_secondary[1] * ratio * 0.4 + c_primary[1] * ratio * 0.6)
        b = int(c_dark[2] * (1 - ratio) + c_secondary[2] * ratio * 0.4 + c_primary[2] * ratio * 0.6)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add abstract luminous glowing shapes
    for _ in range(4):
        cx = random.randint(30, width - 30)
        cy = random.randint(20, height - 20)
        radius = random.randint(25, 60)
        color = random.choice([c_primary, c_accent, c_secondary])
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=color,
            outline=None
        )

    # Soften shapes with Gaussian blur
    base = base.filter(ImageFilter.GaussianBlur(radius=10))

    # Draw modern grid lines & subtle cyber tech texture
    draw = ImageDraw.Draw(base)
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 20), width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, 20), width=1)

    return base

def create_jigsaw_mask(size=48, tab_radius=7):
    """
    Generate an 8-bit alpha mask (L mode) shaped like a classic jigsaw puzzle piece.
    Contains protruding circular tabs on top and right, and an indent on the bottom.
    """
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)

    margin = tab_radius + 2
    inner_size = size - margin * 2

    x0, y0 = margin, margin
    x1, y1 = margin + inner_size, margin + inner_size

    # Inner core rectangle
    draw.rectangle([x0, y0, x1, y1], fill=255)

    # Top tab (protruding outward)
    draw.ellipse(
        [x0 + inner_size // 2 - tab_radius, y0 - tab_radius,
         x0 + inner_size // 2 + tab_radius, y0 + tab_radius],
        fill=255
    )

    # Right tab (protruding outward)
    draw.ellipse(
        [x1 - tab_radius, y0 + inner_size // 2 - tab_radius,
         x1 + tab_radius, y0 + inner_size // 2 + tab_radius],
        fill=255
    )

    # Bottom tab (indent inward)
    draw.ellipse(
        [x0 + inner_size // 2 - tab_radius, y1 - tab_radius,
         x0 + inner_size // 2 + tab_radius, y1 + tab_radius],
        fill=0
    )

    return mask

def generate_captcha_challenge(width=320, height=160, piece_size=48, visual_defense=False):
    """
    Generate a complete Slider Puzzle CAPTCHA challenge.
    Returns:
        challenge_id (str): Unique UUID for session/DB tracking
        target_x (int): Exact X coordinate of target slot (SECRET)
        target_y (int): Exact Y coordinate of target slot
        bg_image_base64 (str): Data URI string of background with slot
        piece_image_base64 (str): Data URI string of cutout piece with alpha
    """
    # 1. Determine target coordinates
    min_x = 65
    max_x = width - piece_size - 20
    min_y = 15
    max_y = height - piece_size - 15

    target_x = random.randint(min_x, max_x)
    target_y = random.randint(min_y, max_y)

    # 2. Generate or load background
    bg_img = generate_procedural_background(width, height)

    # 3. Create Jigsaw mask & find edge boundary
    mask = create_jigsaw_mask(piece_size)
    edges = mask.filter(ImageFilter.FIND_EDGES)

    # 4. Extract puzzle piece
    piece_crop = bg_img.crop((target_x, target_y, target_x + piece_size, target_y + piece_size))
    piece_rgba = Image.new('RGBA', (piece_size, piece_size), (0, 0, 0, 0))
    piece_rgba.paste(piece_crop, (0, 0))
    piece_rgba.putalpha(mask)

    # Add distinct bright border to the piece
    border_layer = Image.new('RGBA', (piece_size, piece_size), (0, 0, 0, 0))
    for px in range(piece_size):
        for py in range(piece_size):
            if edges.getpixel((px, py)) > 100:
                border_layer.putpixel((px, py), (255, 255, 255, 230))
    piece_final = Image.alpha_composite(piece_rgba, border_layer)

    # 5. Create Target Slot on the Background
    bg_rgba = bg_img.convert('RGBA')
    slot_overlay = Image.new('RGBA', (piece_size, piece_size), (10, 15, 25, 200))
    
    # Add a slot outline; the lab defense randomizes its visual signature.
    defense_colors = [
        (251, 113, 133),
        (251, 191, 36),
        (167, 139, 250),
        (232, 121, 249)
    ]
    slot_color = random.choice(defense_colors) if visual_defense else (56, 189, 248)
    for px in range(piece_size):
        for py in range(piece_size):
            if edges.getpixel((px, py)) > 100:
                slot_overlay.putpixel((px, py), (*slot_color, 220))

    bg_rgba.paste(slot_overlay, (target_x, target_y), mask)
    if visual_defense:
        noise = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        noise_draw = ImageDraw.Draw(noise)
        noise_colors = [
            (251, 113, 133, 105),
            (251, 191, 36, 105),
            (167, 139, 250, 105),
            (232, 121, 249, 105)
        ]
        for _ in range(22):
            points = [
                (random.randint(0, width - 1), random.randint(0, height - 1))
                for _ in range(3)
            ]
            noise_draw.line(
                points,
                fill=random.choice(noise_colors),
                width=random.choice((1, 2))
            )
        bg_rgba = Image.alpha_composite(bg_rgba, noise)
        decoy_min_x = 65
        decoy_max_x = width - piece_size - 20
        decoy_positions = [
            x for x in range(decoy_min_x, decoy_max_x + 1)
            if abs(x - target_x) >= piece_size
        ]
        for decoy_x in random.sample(decoy_positions, min(3, len(decoy_positions))):
            for px in range(piece_size):
                for py in range(piece_size):
                    if edges.getpixel((px, py)) > 100:
                        bg_rgba.putpixel(
                            (decoy_x + px, target_y + py),
                            (56, 189, 248, 255)
                        )
    bg_final = bg_rgba.convert('RGB')

    # 6. Convert images to Base64 Data URIs
    # Background as JPEG/PNG
    bg_buffer = io.BytesIO()
    bg_final.save(bg_buffer, format='JPEG', quality=92)
    bg_b64 = "data:image/jpeg;base64," + base64.b64encode(bg_buffer.getvalue()).decode('utf-8')

    # Piece as PNG (requires alpha transparency)
    piece_buffer = io.BytesIO()
    piece_final.save(piece_buffer, format='PNG')
    piece_b64 = "data:image/png;base64," + base64.b64encode(piece_buffer.getvalue()).decode('utf-8')

    challenge_id = uuid.uuid4().hex

    return {
        "challenge_id": challenge_id,
        "target_x": target_x,
        "target_y": target_y,
        "bg_image": bg_b64,
        "piece_image": piece_b64,
        "width": width,
        "height": height,
        "piece_size": piece_size
    }
