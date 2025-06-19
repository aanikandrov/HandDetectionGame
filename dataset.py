import os
import pickle
import cv2
import mediapipe as mp

# Инициализация MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    min_detection_confidence=0.5,  # Повышенный порог уверенности
    max_num_hands=1,  # Ожидаем только одну руку
    min_tracking_confidence=0.5
)

DATA_DIR = './data'

data = []
labels = []
skipped_files = []  # Для отслеживания пропущенных файлов

for dir_ in os.listdir(DATA_DIR):
    dir_path = os.path.join(DATA_DIR, dir_)

    # Пропускаем файлы (если есть)
    if not os.path.isdir(dir_path):
        continue

    for img_name in os.listdir(dir_path):
        img_path = os.path.join(dir_path, img_name)
        img = cv2.imread(img_path)

        # Проверка загрузки изображения
        if img is None:
            print(f"Ошибка загрузки: {img_path}")
            skipped_files.append(img_path)
            continue

        # Конвертация в RGB и изменение размера
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, _ = img.shape

        # Увеличение размера для лучшего распознавания
        if max(height, width) < 500:
            scale_factor = 500 / max(height, width)
            img_rgb = cv2.resize(img_rgb, None, fx=scale_factor, fy=scale_factor)

        # Обработка изображения
        results = hands.process(img_rgb)

        if not results.multi_hand_landmarks:
            skipped_files.append(img_path)
            print(f"Рука не обнаружена: {img_path}")
            continue

        # Обработка только первой обнаруженной руки
        hand_landmarks = results.multi_hand_landmarks[0]
        x_ = [lm.x for lm in hand_landmarks.landmark]
        y_ = [lm.y for lm in hand_landmarks.landmark]

        # Нормализация координат
        min_x, min_y = min(x_), min(y_)
        max_x, max_y = max(x_), max(y_)

        data_aux = []
        for lm in hand_landmarks.landmark:
            # Двойная нормализация: смещение + масштабирование
            data_aux.append((lm.x - min_x) / (max_x - min_x))
            data_aux.append((lm.y - min_y) / (max_y - min_y))

        data.append(data_aux)
        labels.append(dir_)

# Сохранение данных
if data:
    with open('data.pickle', 'wb') as f:
        pickle.dump({'data': data, 'labels': labels}, f)
    print(f"Успешно обработано: {len(data)} изображений")
else:
    print("Данные для сохранения отсутствуют!")

# Отчет о пропущенных файлах
if skipped_files:
    print(f"\nПропущено {len(skipped_files)} изображений:")
    for i, path in enumerate(skipped_files[:5]):  # Первые 5 для примера
        print(f"  {i + 1}. {path}")
    if len(skipped_files) > 5:
        print(f"  ...и еще {len(skipped_files) - 5}")