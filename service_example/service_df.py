# Импортируем класс, от которого будем наследоваться
from service import Service

# Ниже импорты специфичные для задачи
from deepface import DeepFace
import cv2

# Импорт класса для работы с камерой
from cam import Camera


# Определения сервиса для детекции лиц
# Пример как определить свой сервис
class ServiceDF(Service):

    # Функция, которую НЕОБХОДИМО переопределить
    def _do_job(self):
        try:
            # Подключение к RTSP потоку камеры
            url = 'rtsp://0.0.0.0:8554/mystream'  # rtsp-стрим
            url = 0  # webcam
            cap = Camera(url)        

            # Инициализация переменных
            self.__init_vars()

            # "Бесконечный цикл", который выполняют работу, для которой создан сервис:
            # 1) Обработка кадров
            # 2) Обработка звука
            # 3) Обработка сигналов (с лидаров/сонаров)
            while True:
                # ДАННЫЙ БЛОК НЕОБХОДИМО ВКЛЮЧИТЬ В СВОЙ БЕСКОНЕЧНЫЙ ЦИКЛ
                # Начало
                if self.need_job_break:
                    return
                if not self.need_job_pause:
                    continue
                # Конец

                # Получение кадров из потока
                frame_raw = cap.getFrame()
                # Проверка, что кадр непустой
                if frame_raw is None:
                    continue

                # На текущий момент фрейм - это две картинки с RGB-сенсора и со стереопары (Depth) w=1280px, h=480px
                # RGB фрейм слева, т.е. его координаты (x=0, y=0, w=640, h=480)
                # Depth фрейм cghfdf, т.е. его координаты (x=640, y=0, w=640, h=480)
                h, w, ch = frame_raw.shape
                w = w//2
                self.frame = frame_raw[0:h, 0:w]  # получение RGB
                # frame = frame_raw[0:h, w:2*w]  # получение Depth

                # Обработка кадра (или иная работа сервиса)
                # В данном примере работа - это определение лица и его идентификация между кадрами
                result = self.__specific_work()
                 
                # Пример коммуникации с другим Сервисом Б
                # 1) Сервис Б должен прослушивать server_ip:server_port
                # 2) Сервис Б должен уметь обрабатывать команду req (str-type) и возвращать какой-либо результат
                # чтобы обработать результат следует использовать функцию, которая принимает ответ сервиса (str)
                if not result:
                    server_ip = '0.0.0.0'
                    server_port = 0000
                    req = 'same_person'
                    self.run_client(ip=server_ip, port=server_port, request=req, response_handler=self.__resp_hand)
                
                # Пример реализации небольшой задержки и корректного выхода их бесконечного цикла
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:    
            cv2.destroyAllWindows()
            # close job + server
            self.stop()


    # Вспомогательная функция
    def __init_vars(self):
        self._in_target_frames = 0
        self._total_frames = 0

        self._face_rect = None
        self._target = None
        self._target_image = None

    # Вспомогательная функция
    def __specific_work(self):
        print('load deepface...')
        SAME_PERSON = False
        # Our operations on the frame come here
        lst = DeepFace.extract_faces(self.frame, enforce_detection=False, 
                                     detector_backend='mediapipe', align=False, target_size=[256, 256])

        if self._target is None or cv2.waitKey(5) & 0xFF == ord('e'):
            print('Target')
            if lst[0] is not None:
                self._target_image = lst[0]['face']
                self._target = DeepFace.represent(lst[0]['face'].copy(), detector_backend='skip', model_name='ArcFace')

        color = (0, 0, 255)
        THRESH = 0.66
        for i, dict_ in enumerate(lst):
            if dict_['confidence'] < 0.01:
                break
            side_b = DeepFace.represent(dict_['face'], detector_backend='skip', model_name='ArcFace')
            self._face_rect = dict_['facial_area']

            cosine_similarity_score = DeepFace.dst.findCosineDistance(self._target[0]["embedding"], side_b[0]["embedding"])
            print("Cosine Similarity:", cosine_similarity_score)

            if cosine_similarity_score < THRESH:
                self._in_target_frames += 1
                color = (0, 255, 0)
                SAME_PERSON = True

            cv2.imshow(f'Detected_{i}', dict_['face'])
            break
        
        if self._target_image is not None:
            cv2.imshow('Target', self._target_image)
        if self._face_rect is not None:
            cv2.rectangle(self.frame, (self._face_rect['x'], self._face_rect['y']),
                          (self._face_rect['x']+self._face_rect['w'], self._face_rect['y']+self._face_rect['h']), 
                          color, thickness=2)
        cv2.imshow('Frame', self.frame)

        self._total_frames += 1
        print(f'Frames (in/total): {self._in_target_frames}/{self._total_frames}')

        return SAME_PERSON

    def __resp_hand(self, response):
        if response == "goodbye":
            self._target= None
        if response == 'hello':
            self._in_target_frames = 0

    # Функция, которую НЕОБХОДИМО переопределить
    # Обработчик запросов - функция. На вход - строка, на выход (возвращает) - строка
    def _request_handler(self, request):
        # Завести набор команд, которые может обрабатывать сервер
        # Предварительно обозначены следующие команды, которые есть у КАЖДОГО сервиса
        # 1) disable (ставим на паузу)
        # 2) enable (снимаем с паузы)
        # 3) close (закрываем сервис)
        # 4) restart (перезапускаем сервис)

        # остальной набор команд специфичен для каждого сервиса
        # данная функция ВСЕГДА должна что-то возвращать либо результат, либо статус (OK, FAILED, etc)
        some_string = "0"
        return some_string