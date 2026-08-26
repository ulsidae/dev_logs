import cv2
import mediapipe as mp
import numpy as np  # numpy 추가

# Mediapipe 손 인식 초기화
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# 웹캠 캡처
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    # 좌우 반전 및 RGB 변환
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # 손 랜드마크 좌표 리스트
            points = []
            for lm in hand_landmarks.landmark:
                x = int(lm.x * frame.shape[1])
                y = int(lm.y * frame.shape[0])
                points.append([x, y])  # 리스트 형태로 저장해야 np.array() 변환에 문제 없음

            # Convex Hull 및 사각형 트래킹
            if len(points) > 0:
                pts = np.array(points, dtype=np.int32)
                hull = cv2.convexHull(pts)
                x, y, w, h = cv2.boundingRect(hull)

                # 사각형 그리기
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, 'Hand Tracking line', (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 랜드마크 그리기
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # 결과 출력
    cv2.imshow('Hand Tracking', frame)

    # 종료 조건
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 종료 처리
cap.release()
cv2.destroyAllWindows()
