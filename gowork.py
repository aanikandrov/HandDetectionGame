import pickle
import cv2
import mediapipe as mp
import numpy as np

model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Согласование параметров с dataset.py
hands = mp_hands.Hands(
    static_image_mode=True,
    min_detection_confidence=0.5,  # Используем тот же порог
    max_num_hands=1,  # Обрабатываем только одну руку
    min_tracking_confidence=0.5
)

labels_dict = {0: 'palm', 1: 'fist'}

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    H, W, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        # Обрабатываем только первую обнаруженную руку
        hand_landmarks = results.multi_hand_landmarks[0]

        # Рисуем landmarks
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )

        # Собираем координаты
        x_ = [lm.x for lm in hand_landmarks.landmark]
        y_ = [lm.y for lm in hand_landmarks.landmark]

        # Нормализация как в dataset.py
        min_x, min_y = min(x_), min(y_)
        max_x, max_y = max(x_), max(y_)

        data_aux = []
        for lm in hand_landmarks.landmark:
            # Используем такую же нормализацию как при обучении
            if (max_x - min_x) > 0 and (max_y - min_y) > 0:
                data_aux.append((lm.x - min_x) / (max_x - min_x))
                data_aux.append((lm.y - min_y) / (max_y - min_y))
            else:
                # Запасной вариант на случай деления на ноль
                data_aux.append(lm.x)
                data_aux.append(lm.y)

        # Преобразуем в numpy массив
        data_aux = np.asarray(data_aux).reshape(1, -1)

        # Проверка количества признаков
        if data_aux.shape[1] != 42:
            print(f"Предупреждение: получено {data_aux.shape[1]} признаков вместо 42")
            continue

        # Предсказание
        prediction = model.predict(data_aux)
        predicted_character = labels_dict[int(prediction[0])]

        # Отображение результатов
        x1 = int(min_x * W) - 10
        y1 = int(min_y * H) - 10
        x2 = int(max_x * W) + 10
        y2 = int(max_y * H) + 10

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
        cv2.putText(frame, predicted_character, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA)

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()