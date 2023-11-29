from service import Service
import cv2
from cam import Camera

# Need pip install
import yolov5

class ServiceOD(Service):

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
				if self.need_job_break:
					return
				if not self.need_job_pause:
					continue

				# Получение кадров из потока
				self._frame = cap.getFrame()
				# Проверка, что кадр непустой
				if self._frame is None:
					continue

				# Обработка кадра (или иная работа сервиса)
				# В данном примере работа - это определение лица и его идентификация между кадрами
				result = self.__specific_work()
				
				# Пример реализации небольшой задержки и корректного выхода их бесконечного цикла
				if cv2.waitKey(5) & 0xFF == ord('q'):
					break
		
		finally:
			cv2.destroyAllWindows()
			self.stop()


	# Вспомогательная функция
	def __init_vars(self):		
		if not hasattr(self, 'model'):
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
						'giraffe'
						]
			for i in range(len(self.model.names)):
				if self.model.names[i] in alive_set:
					self.model.names[i] = 'alive'

	def __resp_hand(self, response):
		pass

	# Вспомогательная функция
	def __specific_work(self):
		results = self.model(self._frame)
		print(results.pandas())
		return None

	def _request_handler(self, request):
		# Завести набор команд, которые может обрабатывать сервер
		# Предварительно обозначены следующие команды, которые есть у КАЖДОГО сервиса
		# 1) disable (ставим на паузу)
		# 2) enable (снимаем с паузы)
		# 3) close (закрываем сервис)
		# 4) restart (перезапускаем сервис)

		# ЧТО НУЖНО РЕАЛИЗОВАТЬ
		# request `__is_alive_here`, который просто будет возвращать есть ли кто-то живой в кадре???????????
		if request == 'checkAlive':
			results = self.model(self._frame)
			return ('alive' in str(results.tolist()[0]))
		
		if request == 'getFrame':
			pass
	
		# остальной набор команд специфичен для каждого сервиса
		# данная функция ВСЕГДА должна что-то возвращать либо результат, либо статус (OK, FAILED, etc)
		some_string = "0"
		return some_string


