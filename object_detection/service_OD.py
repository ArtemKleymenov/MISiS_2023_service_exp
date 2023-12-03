from service import Service
import cv2
from cam import Camera

# Need pip install
import yolov5

import numpy as np
import base64

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
		if not hasattr(self, 'weights'):
			self.weights = 'yolov5s.pt'

		if not hasattr(self, 'flagActive'):
			self.flagActive = 1

		if not hasattr(self, 'model') or (self.flagActive == 1 and self.model is None):
			self._start_yolo()
	
	def _start_yolo(self):
		self.model = yolov5.load(self.weights)

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
		print(self.model(self._frame))
		return self.model(self._frame)

	def _request_handler(self, request):
		# Предварительно обозначены следующие команды, которые есть у КАЖДОГО сервиса
		# 1) disable (ставим на паузу)
		# 2) enable (снимаем с паузы)
		# 3) close (закрываем сервис)
		# 4) restart (перезапускаем сервис)

		if request == 'checkAlive':
			results = self.model(self._frame)
			return str('alive' in str(results.tolist()[0]))
		
		if request == 'getFrame':
			results = self.model(self._frame)
			data = np.array(results.render()[0]).tobytes()
			_str = base64.b64encode(data)
			return _str.decode()
		
		if request == 'getObjects':
			results = self.model(self._frame)
			keys = [int(pred[-1]) for pred in results.pred[0]]
			values = set(map(results.names.get, keys))
			return ''.join(str(x) + ',' for x in values).strip(',')

		if request == 'getDownNN':
			if self.model is None or self.flagActive == 0:
				return 'failed'
			
			self.model = None
			self.flagActive = 0
			return 'ok'
		
		if request.find('getUpNN_') == 0:
			if self.flagActive == 1:
				return 'failed'
			
			weights = request[8:]

			if len(weights) == 0:
				weights = self.weights
			
			try:
				yolov5.load(weights)
			except:
				return 'failed'

			if self.weights != weights:
				self.weights = weights
			
			self.flagActive = 1
			return 'ok'

		if request.find('applyThreshold_') == 0:
			try:
				value = float(request[15:])
			except:
				return 'failed'
			
			if value > 1 or value < 0:
				return 'failed'
			
			self.model.conf = value
			return 'ok'

		some_string = "0"
		return some_string


