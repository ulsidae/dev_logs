import cv2
import mediapipe as mp
import numpy as np

# 초기화
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

palm_indices = [0, 5, 17, 0]  # 손바닥 사다리꼴용 포인트
finger_joints = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
]

def midpoint(p1, p2):
    return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

def calculate_center_of_mass(points, joints):
    centers = [midpoint(points[a], points[b]) for a, b in joints]
    x_avg = sum(p[0] for p in centers) // len(centers)
    y_avg = sum(p[1] for p in centers) // len(centers)
    return (x_avg, y_avg)

def compute_torque(wrist, prev_pos, curr_pos):
    r = np.array([curr_pos[0] - wrist[0], curr_pos[1] - wrist[1]])
    F = np.array([curr_pos[0] - prev_pos[0], curr_pos[1] - prev_pos[1]])
    torque = r[0]*F[1] - r[1]*F[0]
    return torque

def draw_finger_rectangles(frame, points):
    finger_bases = [(0, 1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12),
                    (13, 14, 15, 16), (17, 18, 19, 20)]
    for finger in finger_bases:
        for i in range(len(finger) - 1):
            p1, p2 = points[finger[i]], points[finger[i+1]]
            cv2.rectangle(frame, p1, p2, (100, 100, 255), 2)

prev_finger_tips = None

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            landmarks = hand_landmarks.landmark
            points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
            wrist = points[0]

            # 손바닥 사다리꼴
            palm_pts = [points[i] for i in palm_indices]
            cv2.polylines(frame, [np.array(palm_pts)], isClosed=True, color=(255, 0, 0), thickness=2)

            # 손가락 사각형 (막대) 표현
            draw_finger_rectangles(frame, points)

            # 관절 연결 및 점
            for a, b in finger_joints:
                cv2.line(frame, points[a], points[b], (0, 255, 0), 4)
                cv2.circle(frame, points[a], 4, (0, 0, 255), -1)

            # 질량 중심
            com = calculate_center_of_mass(points, finger_joints)
            cv2.circle(frame, com, 8, (255, 255, 0), -1)
            cv2.putText(frame, 'P', (com[0]+10, com[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

            # 회전력 시각화
            finger_tips = [points[i] for i in [4, 8, 12, 16, 20]]
            if prev_finger_tips:
                for i, (prev, curr) in enumerate(zip(prev_finger_tips, finger_tips)):
                    torque = compute_torque(wrist, prev, curr)
                    cv2.arrowedLine(frame, wrist, curr, (0, 255, 255), 2, tipLength=0.2)
                    cv2.putText(frame, f"T{i}:{int(torque)}", (curr[0], curr[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)
            prev_finger_tips = finger_tips

            # 랜드마크 전체 그리기
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Hand Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
