import math
import threading
import time
import cv2
import mss
import numpy as np
import pydirectinput
import pygetwindow as gw
import keyboard



GAME_X = 0
GAME_Y = 0
GAME_W = 640
GAME_H = 480

BRIGHTNESS_THRESHOLD = 200
PLAYER_HITBOX_RADIUS = 2.0
SAFE_MARGIN = 8.0
MOVE_INTERVAL = 0.016


running = False

current_dir_x = 0
current_dir_y = 0
is_slow = False

last_control_time = 0.0

prev_bullets = []
bullet_tracks = {}

next_bullet_id = 0

last_known_player_pos = None
player_confidence = 0.0

last_frame_time = time.perf_counter()

game_x = GAME_X
game_y = GAME_Y
game_w = GAME_W
game_h = GAME_H

sct = mss.MSS()


PLAYER_MIN_Y = 0.48
PLAYER_MAX_Y = 0.98
PLAYER_SEARCH_RADIUS = 70

PLAYER_MARGIN_X = 18
PLAYER_MARGIN_TOP = 20
PLAYER_MARGIN_BOTTOM = 12

BULLET_MIN_AREA = 2
BULLET_MAX_AREA = 180
BULLET_MAX_TRACK_DISTANCE = 45

THREAT_DISTANCE = 150
EXTRA_SAFETY_MARGIN = 8
PREDICTION_FRAMES = 30
FAR_PREDICTION_WEIGHT = 0.35

NORMAL_STEP = 12.0
FAST_STEP = 20.0
SLOW_STEP = 5.0
CONTROL_INTERVAL = 0.035
DIRECTION_STICK_TIME = 0.10

HOME_X_RATIO = 0.50
HOME_Y_RATIO = 0.84
LOWER_LIMIT_RATIO = 0.58

EMERGENCY_DISTANCE = 42
CRITICAL_DISTANCE = 25
SLOW_DANGER_DISTANCE = 65


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def update_window_position():
    global game_x, game_y, game_w, game_h
    global last_known_player_pos

    windows = gw.getWindowsWithTitle("th18")

    if not windows:
        windows = [
            w
            for w in gw.getAllWindows()
            if "th18" in w.title.lower()
               or "touhou" in w.title.lower()
        ]

    if windows:
        win = windows[0]

        if win.isMinimized:
            win.restore()
            time.sleep(0.2)

        win_w = win.width if win.width > 0 else 640
        win_h = win.height if win.height > 0 else 480

        scale_x = win_w / 640.0
        scale_y = win_h / 480.0

        field_w = int(384 * scale_x)
        field_h = int(448 * scale_y)

        border_x = int(32 * scale_x)
        title_y = int(42 * scale_y)

        game_x = int(win.left + border_x)
        game_y = int(win.top + title_y)
        game_w = field_w
        game_h = field_h

        print(
            f"\n[Window] "
            f"x={game_x} y={game_y} "
            f"w={game_w} h={game_h} "
            f"scale={scale_x:.2f},{scale_y:.2f}"
        )

    else:
        game_x = GAME_X
        game_y = GAME_Y
        game_w = GAME_W
        game_h = GAME_H
        print(
            f"\n[WARN] Window not found. "
            f"Using config: "
            f"{game_x},{game_y} {game_w}x{game_h}"
        )

    last_known_player_pos = (
        game_w * HOME_X_RATIO,
        game_h * HOME_Y_RATIO,
    )

def capture():
    monitor = {
        "left": int(game_x),
        "top": int(game_y),
        "width": int(game_w),
        "height": int(game_h),
    }
    frame = np.array(sct.grab(monitor))
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

def estimate_player_pos(frame):
    global last_known_player_pos
    global player_confidence

    h, w = frame.shape[:2]

    if last_known_player_pos is None:
        last_known_player_pos = (w * HOME_X_RATIO, h * HOME_Y_RATIO)

    lx, ly = last_known_player_pos

    x1 = int(clamp(lx - PLAYER_SEARCH_RADIUS, 0, w - 1))
    x2 = int(clamp(lx + PLAYER_SEARCH_RADIUS, 1, w))
    y1 = int(clamp(max(h * PLAYER_MIN_Y, ly - PLAYER_SEARCH_RADIUS), 0, h - 1))
    y2 = int(clamp(min(h * PLAYER_MAX_Y, ly + PLAYER_SEARCH_RADIUS), 1, h))

    roi = frame[y1:y2, x1:x2]

    if roi.size == 0:
        player_confidence *= 0.9
        return last_known_player_pos

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    bright = cv2.inRange(hsv, np.array([0, 35, 130]), np.array([179, 255, 255]))
    kernel = np.ones((2, 2), np.uint8)
    bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel)

    cnts = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = cnts[0] if len(cnts) == 2 else cnts[1]

    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 2 or area > 120:
            continue

        bx, by, bw, bh = cv2.boundingRect(contour)
        if bw > 25 or bh > 25:
            continue

        cx = x1 + bx + bw / 2
        cy = y1 + by + bh / 2
        d = math.hypot(cx - lx, cy - ly)
        score = d

        if cy < h * 0.60:
            score += 30

        candidates.append((score, cx, cy))

    if candidates:
        candidates.sort(key=lambda x: x[0])
        _, px, py = candidates[0]
        movement = math.hypot(px - lx, py - ly)

        if movement <= PLAYER_SEARCH_RADIUS * 1.25:
            alpha = 0.65
            px = lx * (1 - alpha) + px * alpha
            py = ly * (1 - alpha) + py * alpha
            last_known_player_pos = (px, py)
            player_confidence = min(1.0, player_confidence + 0.15)
            return px, py

    player_confidence *= 0.92
    return last_known_player_pos

def detect_bullets(frame, player_pos):
    global prev_bullets
    global bullet_tracks
    global next_bullet_id

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0, 25, BRIGHTNESS_THRESHOLD]), np.array([179, 255, 255]))
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    px, py = player_pos
    cv2.circle(mask, (int(px), int(py)), 18, 0, -1)

    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = cnts[0] if len(cnts) == 2 else cnts[1]

    detected = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < BULLET_MIN_AREA or area > BULLET_MAX_AREA:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w > 28 or h > 28:
            continue

        cx = x + w / 2
        cy = y + h / 2

        if cx < 3 or cx > game_w - 3 or cy < 3 or cy > game_h - 3:
            continue

        r = max(w, h) / 2
        detected.append({"x": cx, "y": cy, "r": max(2.0, r)})

    new_tracks = {}
    used_old = set()

    for bullet in detected:
        best_id = None
        best_dist = BULLET_MAX_TRACK_DISTANCE

        for track_id, old in bullet_tracks.items():
            if track_id in used_old:
                continue

            d = math.hypot(bullet["x"] - old["x"], bullet["y"] - old["y"])
            if d < best_dist:
                best_dist = d
                best_id = track_id

        if best_id is not None:
            old = bullet_tracks[best_id]
            vx = bullet["x"] - old["x"]
            vy = bullet["y"] - old["y"]
            vx = old["vx"] * 0.35 + vx * 0.65
            vy = old["vy"] * 0.35 + vy * 0.65
            track_id = best_id
            used_old.add(track_id)
        else:
            track_id = next_bullet_id
            next_bullet_id += 1
            vx = 0.0
            vy = 0.0

        new_tracks[track_id] = {
            "x": bullet["x"],
            "y": bullet["y"],
            "vx": vx,
            "vy": vy,
            "r": bullet["r"],
            "age": bullet_tracks.get(track_id, {}).get("age", 0) + 1,
        }

    bullet_tracks = new_tracks
    result = list(bullet_tracks.values())
    prev_bullets = result
    return result

def predict_bullet(bullet, t):
    return (bullet["x"] + bullet["vx"] * t, bullet["y"] + bullet["vy"] * t)

def evaluate_point_risk(px, py, bullets, current_x, current_y):
    risk = 0.0

    left_margin = PLAYER_MARGIN_X
    right_margin = game_w - PLAYER_MARGIN_X
    top_margin = int(game_h * 0.32)
    bottom_margin = game_h - PLAYER_MARGIN_BOTTOM

    if px < left_margin:
        risk += (left_margin - px) ** 2 * 4.0
    if px > right_margin:
        risk += (px - right_margin) ** 2 * 4.0
    if py < top_margin:
        risk += (top_margin - py) ** 2 * 2.5
    if py > bottom_margin:
        risk += (py - bottom_margin) ** 2 * 4.0

    for bullet in bullets:
        current_distance = math.hypot(bullet["x"] - px, bullet["y"] - py)
        if current_distance > THREAT_DISTANCE:
            continue

        collision_radius = PLAYER_HITBOX_RADIUS + bullet["r"] + EXTRA_SAFETY_MARGIN
        minimum_distance = float("inf")

        for t in range(1, PREDICTION_FRAMES + 1):
            bx, by = predict_bullet(bullet, t)
            d = math.hypot(bx - px, by - py)
            if d < minimum_distance:
                minimum_distance = d
            if d <= collision_radius:
                time_weight = (PREDICTION_FRAMES - t + 1) / PREDICTION_FRAMES
                risk += (100000.0 * (0.5 + time_weight))
                break

        safe_distance = collision_radius + SAFE_MARGIN
        if minimum_distance < safe_distance:
            danger = safe_distance - minimum_distance
            risk += (danger ** 2 * 80.0)

        rel_x = px - bullet["x"]
        rel_y = py - bullet["y"]
        speed = math.hypot(bullet["vx"], bullet["vy"])

        if speed > 0.5:
            dot = bullet["vx"] * rel_x + bullet["vy"] * rel_y
            if dot > 0:
                risk += (120.0 / max(current_distance, 10))

    movement = math.hypot(px - current_x, py - current_y)
    risk += movement * 0.04

    home_x = game_w * HOME_X_RATIO
    home_y = game_h * HOME_Y_RATIO
    home_distance = math.hypot(px - home_x, py - home_y)
    risk += home_distance * 0.045

    lower_limit = game_h * LOWER_LIMIT_RATIO
    if py < lower_limit:
        upward_distance = lower_limit - py
        risk += upward_distance * 0.20

    return risk

def analyze_danger(px, py, bullets):
    danger_left = 0.0
    danger_right = 0.0
    danger_up = 0.0
    danger_down = 0.0
    nearest = float("inf")
    critical = False
    dangerous = False

    for b in bullets:
        dx = b["x"] - px
        dy = b["y"] - py
        d = math.hypot(dx, dy)

        if d < nearest:
            nearest = d
        if d > THREAT_DISTANCE:
            continue

        weight = (max(0.0, THREAT_DISTANCE - d) / THREAT_DISTANCE) ** 2

        if dx < 0:
            danger_left += weight
        else:
            danger_right += weight
        if dy < 0:
            danger_up += weight
        else:
            danger_down += weight

        if b["vy"] > 0:
            danger_down += weight * 1.8
        elif b["vy"] < 0:
            danger_up += weight * 1.2

        if b["vx"] > 0:
            danger_right += weight * 0.8
        elif b["vx"] < 0:
            danger_left += weight * 0.8

        if d < CRITICAL_DISTANCE:
            critical = True
        elif d < EMERGENCY_DISTANCE:
            dangerous = True

    return {
        "left": danger_left,
        "right": danger_right,
        "up": danger_up,
        "down": danger_down,
        "nearest": nearest,
        "critical": critical,
        "dangerous": dangerous,
    }

def generate_candidates(px, py, danger):
    candidates = []
    candidates.append((px, py, "stay"))

    for step in [SLOW_STEP, NORMAL_STEP, FAST_STEP, FAST_STEP * 1.5]:
        candidates.append((px - step, py, "left"))
        candidates.append((px + step, py, "right"))
        candidates.append((px, py - step, "up"))
        candidates.append((px, py + step, "down"))

    for step in [NORMAL_STEP, FAST_STEP]:
        candidates.extend([
            (px - step, py - step, "up_left"),
            (px + step, py - step, "up_right"),
            (px - step, py + step, "down_left"),
            (px + step, py + step, "down_right"),
        ])

    candidates.extend([
        (game_w * 0.18, py, "far_left"),
        (game_w * 0.82, py, "far_right"),
        (px, game_h * 0.65, "far_up"),
        (px, game_h * 0.90, "far_down"),
    ])

    return candidates

def search_best_action(px, py, bullets):
    danger = analyze_danger(px, py, bullets)
    candidates = generate_candidates(px, py, danger)

    best = None
    best_risk = float("inf")

    for cx, cy, action in candidates:
        cx = clamp(cx, PLAYER_MARGIN_X, game_w - PLAYER_MARGIN_X)
        cy = clamp(cy, int(game_h * 0.30), game_h - PLAYER_MARGIN_BOTTOM)

        risk = evaluate_point_risk(cx, cy, bullets, px, py)

        if "left" in action:
            risk += danger["left"] * 80.0
        if "right" in action:
            risk += danger["right"] * 80.0
        if "up" in action:
            risk += danger["up"] * 70.0
        if "down" in action:
            risk += danger["down"] * 70.0

        if action == "left" and danger["left"] > danger["right"]:
            risk += 500.0
        elif action == "right" and danger["right"] > danger["left"]:
            risk += 500.0
        elif action == "up" and danger["up"] > danger["down"]:
            risk += 300.0
        elif action == "down" and danger["down"] > danger["up"]:
            risk += 300.0

        if not danger["dangerous"] and cy < game_h * 0.65:
            risk += (game_h * 0.65 - cy) * 0.35

        movement = math.hypot(cx - px, cy - py)
        risk += movement * 0.08

        if risk < best_risk:
            best_risk = risk
            best = (cx, cy, action, danger, best_risk)

    return best

def target_to_direction(px, py, tx, ty, danger):
    dx = tx - px
    dy = ty - py
    DEADZONE = 4.0

    dir_x = 0
    dir_y = 0

    if abs(dx) > DEADZONE:
        dir_x = -1 if dx < 0 else 1

    if abs(dy) > DEADZONE:
        dir_y = -1 if dy < 0 else 1

    if danger["critical"]:
        horizontal_bias = danger["right"] - danger["left"]
        vertical_bias = danger["down"] - danger["up"]

        if abs(horizontal_bias) > abs(vertical_bias):
            dir_x = 1 if danger["left"] > danger["right"] else -1
        else:
            dir_y = 1 if danger["up"] > danger["down"] else -1

    return dir_x, dir_y

def set_controls(dir_x, dir_y, slow):
    global current_dir_x
    global current_dir_y
    global is_slow
    global last_control_time

    now = time.perf_counter()

    if (dir_x == current_dir_x and dir_y == current_dir_y and slow == is_slow):
        return

    if now - last_control_time < CONTROL_INTERVAL:
        return

    # X Control
    if dir_x != current_dir_x:
        if current_dir_x == -1:
            pydirectinput.keyUp("left")
        elif current_dir_x == 1:
            pydirectinput.keyUp("right")

        if dir_x == -1:
            pydirectinput.keyDown("left")
        elif dir_x == 1:
            pydirectinput.keyDown("right")

        current_dir_x = dir_x

    # Y Control
    if dir_y != current_dir_y:
        if current_dir_y == -1:
            pydirectinput.keyUp("up")
        elif current_dir_y == 1:
            pydirectinput.keyUp("down")

        if dir_y == -1:
            pydirectinput.keyDown("up")
        elif dir_y == 1:
            pydirectinput.keyDown("down")

        current_dir_y = dir_y

    # Shift (Slow Mode)
    if slow != is_slow:
        if slow:
            pydirectinput.keyDown("shift")
        else:
            pydirectinput.keyUp("shift")
        is_slow = slow

    last_control_time = now

def release_keys():
    global current_dir_x
    global current_dir_y
    global is_slow

    for key in ["left", "right", "up", "down", "shift", "z"]:
        try:
            pydirectinput.keyUp(key)
        except:
            pass

    current_dir_x = 0
    current_dir_y = 0
    is_slow = False

def bot_loop():
    global running
    global bullet_tracks
    global prev_bullets

    update_window_position()
    bullet_tracks = {}
    prev_bullets = []

    print("\n[AI v3 Started]"
          "\n  - Player local tracking"
          "\n  - Bullet velocity tracking"
          "\n  - PyDirectInput Applied\n")

    pydirectinput.keyDown("z")
    frame_counter = 0

    try:
        while running:
            frame_start = time.perf_counter()
            frame = capture()
            px, py = estimate_player_pos(frame)
            bullets = detect_bullets(frame, (px, py))
            result = search_best_action(px, py, bullets)

            if result is not None:
                tx, ty, action, danger, risk = result
                dx, dy = target_to_direction(px, py, tx, ty, danger)

                nearest = danger["nearest"]
                if nearest < CRITICAL_DISTANCE:
                    slow = False
                elif nearest < SLOW_DANGER_DISTANCE:
                    slow = True
                else:
                    slow = True

                if not danger["dangerous"]:
                    home_x = game_w * HOME_X_RATIO
                    home_y = game_h * HOME_Y_RATIO
                    hx = home_x - px
                    hy = home_y - py
                    dx = 1 if hx > 0 else -1 if abs(hx) > 8 else 0
                    dy = 1 if hy > 0 else -1 if abs(hy) > 8 else 0
                    slow = True

                set_controls(dx, dy, slow)
            else:
                danger = {"nearest": float("inf"), "dangerous": False, "critical": False}
                set_controls(0, 0, True)

            frame_counter += 1
            if frame_counter % 2 == 0:
                nearest_text = f"{danger['nearest']:.1f}" if math.isfinite(danger["nearest"]) else "---"
                print(
                    f"\rP=({px:3.0f},{py:3.0f}) B={len(bullets):3d} Near={nearest_text:>6} D=({current_dir_x:+d},{current_dir_y:+d}) Slow={is_slow} Conf={player_confidence:.2f}        ",
                    end="", flush=True)

            elapsed = time.perf_counter() - frame_start
            time.sleep(max(0.005, MOVE_INTERVAL - elapsed))

    finally:
        release_keys()
        print("\n[AI v3 Stopped]")

def main():
    global running

    print("=========================================")
    print("Touhou18 AI Dodge Experiment")
    print("=========================================")
    print("F6 : Start")
    print("F7 : Stop")
    print("F2 : Exit\n")

    def start():
        global running
        if not running:
            running = True
            threading.Thread(target=bot_loop, daemon=True).start()

    def stop():
        global running
        running = False
        release_keys()

    keyboard.add_hotkey("f6", start)
    keyboard.add_hotkey("f7", stop)
    keyboard.wait("f2")
    stop()


if __name__ == "__main__":
    main()
