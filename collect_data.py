import os

import cv2

# TODO разбор
# TODO вынести в Qt
# TODO таймер и количество изображений
# TODO зеркальное отображение как опция


DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

number_of_classes = 2
dataset_size = 200
wait = 100 # задержка между кадрами

cap = cv2.VideoCapture(0)



for j in range(number_of_classes):
    if not os.path.exists(os.path.join(DATA_DIR, str(j))):
        os.makedirs(os.path.join(DATA_DIR, str(j)))

    print('Collecting data for class {}'.format(j))

    done = False
    while True:
        ret, frame = cap.read()

        frame = cv2.flip(frame, 1)

        cv2.putText(frame, 'Ready? Press "Q" ! :)', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3,
                    cv2.LINE_AA)
        cv2.imshow('frame', frame)
        if cv2.waitKey(wait) == ord('q'):
            break

    counter = 0
    while counter < dataset_size:
        ret, frame = cap.read()

        # Зеркальное отображение
        frame = cv2.flip(frame, 1)

        cv2.imshow('frame', frame)
        cv2.waitKey(wait)
        cv2.imwrite(os.path.join(DATA_DIR, str(j), '{}.jpg'.format(counter)), frame)

        counter += 1

cap.release()
cv2.destroyAllWindows()