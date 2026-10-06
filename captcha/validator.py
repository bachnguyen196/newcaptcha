import time
from config import Config
from database.db import get_challenge, mark_challenge_used

def validate_slider_captcha(challenge_id, user_x):
    """
    Validate Slider Puzzle CAPTCHA on the Backend (Strict Server-Side Security).

    Security Rules:
    1. Zero-Trust Frontend: Target_X is never revealed to the client.
    2. Single-Use Token: Challenge is immediately invalidated to prevent Replay Attacks.
    3. Time-To-Live (TTL): Challenges expire after Config.CAPTCHA_TTL_SECONDS (120s).
    4. Tolerance Threshold: Checks if user coordinate matches within allowed margin.

    Returns:
        (is_valid: bool, reason: str)
        Possible reasons:
        - "PASS": Successfully solved
        - "WRONG_POSITION": Coordinate offset exceeds tolerance
        - "REPLAY_ATTACK": Challenge ID was already consumed
        - "EXPIRED": Challenge exceeded allowed TTL
        - "INVALID_CHALLENGE": Challenge ID does not exist in DB
        - "INVALID_INPUT": Missing or malformed parameters
    """
    if not challenge_id:
        return False, "INVALID_INPUT"

    challenge = get_challenge(challenge_id)
    if not challenge:
        return False, "INVALID_CHALLENGE"

    # 1. Anti-Replay Check: Was it already used?
    if challenge['used'] == 1:
        return False, "REPLAY_ATTACK"

    # 2. Mark as used IMMEDIATELY to prevent race conditions & re-use
    mark_challenge_used(challenge_id)

    # 3. Expiration / TTL Check
    created_at = challenge['created_at']
    elapsed = time.time() - created_at
    if elapsed > Config.CAPTCHA_TTL_SECONDS:
        return False, "EXPIRED"

    # 4. Parse user coordinate
    try:
        user_x_val = float(user_x)
    except (ValueError, TypeError):
        return False, "INVALID_INPUT"

    # 5. Tolerance Validation
    target_x = challenge['target_x']
    diff = abs(user_x_val - target_x)

    if diff <= Config.CAPTCHA_TOLERANCE:
        return True, "PASS"
    else:
        return False, "WRONG_POSITION"
