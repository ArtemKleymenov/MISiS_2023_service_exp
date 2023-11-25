#### MISiS_2023_service_exp
Fall 2023 MISiS. Robot prj. Service example for participants 

## Пример создания и работы с сервисом

В файле `service.py` определён базовый класс для работы с сервисами для проекта Абитубот.   
В директории `service_example` представлен пример создания сервиса по детекции/идентификации лиц (`service_df.py`), а также запуск такого сервиса (`run.py`).

В файлах добавлены комментарии, сопровождающие код. Настоятельно рекомендуется ознакомиться с файлами `service_df.py` и `run.py`. 

## Troubleshooting

Если при запуске скрипта/сервиса, возникает ошибка
> ModuleNotFoundError: No module named 'service'


~~то следует вызвать команду (рекомендуется использовать виртуальное окружение)~~
~~> pip install -e .~~


Добавить перед импортом сервиса (`from service import Service`) следующие строки:
> import sys


> import os


> dir_path = os.path.dirname(os.path.realpath(__file__))    # Для запуска сервиса используем


> sys.path.append(f"{dir_path}/..")


## Дополнение

Внесение изменений и правок в данный репозиторий возможно через `Issues`.
