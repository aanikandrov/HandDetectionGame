import os
import cv2
import pickle
import argparse
import numpy as np
import mediapipe as mp
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from PIL import ImageFont, ImageDraw, Image


def collect_data():
    """Сбор датасета жестов пользователя с помощью камеры """

    try:
        DATA_DIR = 'data'
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        number_of_classes = 2 # Количество классов (жестов)
        dataset_size = 200    # Количество изображений для одного класса
        wait = 100            # Задержка между кадрами (мс)

        cap = cv2.VideoCapture(0) # Захват камеры

        for j in range(number_of_classes):
            class_dir = os.path.join(DATA_DIR, str(j))
            if not os.path.exists(class_dir):
                os.makedirs(class_dir)

            print(f'Сбор данных для класса {j}')

            # Ожидание готовности пользователя
            while True:
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)  # Зеркальное отражение

                # Определение текста в зависимости от значения j
                if j == 0:
                    instruction_text = 'Готовы? Нажмите "Q" \nи затем покажите открытую ладонь\nв разных позициях с разных сторон'
                else:
                    instruction_text = 'Готовы? Нажмите "Q" \nи затем покажите сжатый кулак\nв разных позициях с разных сторон '

                # Преобразование изображения в формат PIL
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_img)

                font = ImageFont.truetype("arial.ttf", 32)

                # Отображение инструкции
                draw.text((10, 10), instruction_text, font=font, fill=(255, 165, 0))

                # Преобразование обратно в формат OpenCV
                frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                cv2.imshow('frame', frame)
                key = cv2.waitKey(1)
                if key == ord('q'):
                    break

            # Сбор изображений
            counter = 0
            while counter < dataset_size:
                ret, frame = cap.read()
                frame = cv2.flip(frame, 1)  # Зеркальное отражение

                progress = int((counter / dataset_size) * 100)
                progress_text = f'Progress: {progress}%'
                cv2.putText(
                    frame, progress_text, (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA
                )

                cv2.imshow('frame', frame)

                cv2.imshow('frame', frame)
                cv2.waitKey(wait)

                # Сохранение изображения
                img_path = os.path.join(class_dir, f'{counter}.jpg')
                cv2.imwrite(img_path, frame)
                counter += 1

        cap.release()
        cv2.destroyAllWindows()
        print("Сбор данных завершен!")

    except Exception as e:
        print(f"Ошибка в collect_data: {str(e)}")

    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()


def create_dataset():
    """ Разметка датасета на основе изображений с помощью MediaPipe """

    # Инициализация MediaPipe Hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        min_detection_confidence=0.5,
        max_num_hands=1,
        min_tracking_confidence=0.5
    )

    DATA_DIR = 'data'
    data = []
    labels = []
    skipped_files = []  # Для отслеживания пропущенных файлов

    # Обработка всех изображений в директориях классов
    for class_dir in os.listdir(DATA_DIR):
        class_path = os.path.join(DATA_DIR, class_dir)

        # Пропуск файлов (если есть)
        if not os.path.isdir(class_path):
            continue

        for img_name in os.listdir(class_path):
            img_path = os.path.join(class_path, img_name)
            img = cv2.imread(img_path)

            # Проверка загрузки изображения
            if img is None:
                print(f"Ошибка загрузки: {img_path}")
                skipped_files.append(img_path)
                continue

            # Конвертация в RGB
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
            labels.append(class_dir)

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


def train_model():
    """ Обучение модели классификации жестов """
    # Загрузка данных
    data_dict = pickle.load(open('data.pickle', 'rb'))
    data = np.asarray(data_dict['data'])
    labels = np.asarray(data_dict['labels'])

    # Разделение данных на обучающую и тестовую выборки
    x_train, x_test, y_train, y_test = train_test_split(
        data, labels, test_size=0.2, shuffle=True, stratify=labels
    )

    # Создание и обучение модели
    model = RandomForestClassifier()
    model.fit(x_train, y_train)

    # Оценка точности модели
    y_predict = model.predict(x_test)
    score = accuracy_score(y_predict, y_test)
    print(f'Точность модели: {score * 100:.2f}%')

    # Сохранение обученной модели
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'Model')
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, 'model.p')

    with open(model_path, 'wb') as f:
        pickle.dump({'model': model}, f)
    print(f"Модель сохранена в {model_path}")


def test_model():
    """ Тестирование модели в реальном времени с помощью камеры """
    # Загрузка обученной модели
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'Model')
    model_path = os.path.join(model_dir, 'model.p')

    model_dict = pickle.load(open(model_path, 'rb'))
    model = model_dict['model']

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Ошибка: Не удалось открыть камеру.")
        return

    # Инициализация MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(
        static_image_mode=True,
        min_detection_confidence=0.5,
        max_num_hands=1,
        min_tracking_confidence=0.5
    )

    labels_dict = {0: 'palm', 1: 'fist'}  # Словарь жестов

    print("Запуск распознавания жестов. Нажмите 'q' для выхода.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        H, W, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            # Обработка первой обнаруженной руки
            hand_landmarks = results.multi_hand_landmarks[0]

            # Отрисовка landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            # Сбор координат
            x_ = [lm.x for lm in hand_landmarks.landmark]
            y_ = [lm.y for lm in hand_landmarks.landmark]

            # Нормализация координат
            min_x, min_y = min(x_), min(y_)
            max_x, max_y = max(x_), max(y_)

            data_aux = []
            for lm in hand_landmarks.landmark:
                # Нормализация как при обучении
                if (max_x - min_x) > 0 and (max_y - min_y) > 0:
                    data_aux.append((lm.x - min_x) / (max_x - min_x))
                    data_aux.append((lm.y - min_y) / (max_y - min_y))
                else:
                    # Запасной вариант
                    data_aux.append(lm.x)
                    data_aux.append(lm.y)

            # Преобразование в numpy массив
            data_aux = np.asarray(data_aux).reshape(1, -1)

            # Проверка количества признаков
            if data_aux.shape[1] != 42:
                print(f"Предупреждение: получено {data_aux.shape[1]} признаков вместо 42")
                continue

            # Предсказание жеста
            prediction = model.predict(data_aux)
            predicted_gesture = labels_dict[int(prediction[0])]

            # Отображение результатов
            x1 = int(min_x * W) - 10
            y1 = int(min_y * H) - 10
            x2 = int(max_x * W) + 10
            y2 = int(max_y * H) + 10

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
            cv2.putText(
                frame, predicted_gesture, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3, cv2.LINE_AA
            )

        cv2.imshow('Распознавание жестов', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()