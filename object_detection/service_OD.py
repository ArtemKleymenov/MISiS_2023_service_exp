# Импортируем класс, от которого будем наследоваться
from service import Service

# Ниже импорты специфичные для задачи
import cv2

import yolov5

# Импорт класса для работы с камерой
from cam import Camera


# Определения сервиса для детекции лиц
# Пример как определить свой сервис
class ServiceOD(Service):

	# Функция, которую НЕОБХОДИМО переопределить
	def _do_job(self):
		try:
			# Подключение к RTSP потоку камеры
			#url = 'rtsp://0.0.0.0:8554/mystream'  # rtsp-стрим
			url = 0  # webcam
			cap = Camera(url)
			self.url = url

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
				self.frame = frame_raw[:, :]  # получение RGB
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
					req = 'no_frame'
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
				
		self.model = yolov5.load('yolov5s.pt')
		# set model parameters
		self.model.conf = 0.25  # NMS confidence threshold
		self.model.iou = 0.45  # NMS IoU threshold
		self.model.agnostic = False  # NMS class-agnostic
		self.model.multi_label = False  # NMS multiple labels per box
		self.model.max_det = 1000  # maximum number of detections per image

		alive_set = ['person',
					'bird',
					'cat',
					'dog',
					'horse',
					'sheep',
					'cow',
					'elephant',
					'bear',
					'zebra',
					'giraffe',
					]
		for i in range(len(self.model.names)):
			if self.model.names[i] in alive_set:
				self.model.names[i] = 'alive'

	def __resp_hand(self, response):
		if response == "goodbye":
			self._target= None
		if response == 'hello':
			self._in_target_frames = 0

	# Вспомогательная функция
	def __specific_work(self):
		print('load YOLO...')
		results = self.model(self.frame)
		return ('alive' in str(results.tolist()[0]))

	def _request_handler(self, request):
		# Завести набор команд, которые может обрабатывать сервер
		# Предварительно обозначены следующие команды, которые есть у КАЖДОГО сервиса
		# 1) disable (ставим на паузу)
		# 2) enable (снимаем с паузы)
		# 3) close (закрываем сервис)
		# 4) restart (перезапускаем сервис)

		# ЧТО НУЖНО РЕАЛИЗОВАТЬ
		# request `__is_alive_here`, который просто будет возвращать есть ли кто-то живой в кадре
		if request == 'is_alive_here':
			output = self._do_job()
		
		# остальной набор команд специфичен для каждого сервиса
		# данная функция ВСЕГДА должна что-то возвращать либо результат, либо статус (OK, FAILED, etc)
		some_string = "0"
		return some_string


