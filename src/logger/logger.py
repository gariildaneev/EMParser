import logging
from logging.handlers import RotatingFileHandler


class Logger:
    """Класс для настройки единственного экземпляра логгера (Singleton)."""

    _instance = None  # Переменная для хранения единственного экземпляра логгера

    def __new__(cls):
        """Реализуем Singleton: создаём только один экземпляр логгера."""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Настраивает логгер."""
        self.logger = logging.getLogger("ParserLogger")
        self.logger.setLevel(logging.DEBUG)  # Общий уровень логов (для файла)

        # 🔹 Формат для файла (подробный)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 🔹 Формат для терминала (более читаемый)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )

        # 🔹 Обработчик для файла (всё пишем в файл)
        file_handler = RotatingFileHandler("parser.log", maxBytes=5_000_000, backupCount=3)
        file_handler.setLevel(logging.DEBUG)  # В файл пишем ВСЕ уровни логов
        file_handler.setFormatter(file_formatter)

        # 🔹 Обработчик для консоли (только INFO+)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # В консоль пишем только INFO и выше
        console_handler.setFormatter(console_formatter)

        # Добавляем обработчики в логгер
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Возвращает единственный экземпляр логгера."""
        return self.logger


# Создание единственного экземпляра логгера
parser_logger = Logger().get_logger()

# # 📌 УРОВНИ ЛОГИРОВАНИЯ:
#
# # 1️⃣ DEBUG (уровень 10) – Отладочная информация, используется для диагностики кода
# parser_logger.debug("Отладочное сообщение: переменная X = 42")
#
# # 2️⃣ INFO (уровень 20) – Основные события, показывают нормальное поведение программы
# parser_logger.info("Программа запущена")
#
# # 3️⃣ WARNING (уровень 30) – Возможная проблема, которая не критична, но требует внимания
# parser_logger.warning("Внимание: Долгое время ответа сервера")
#
# # 4️⃣ ERROR (уровень 40) – Ошибка, но программа продолжает работать
# parser_logger.error("Ошибка: Файл не найден")
#
# # 5️⃣ CRITICAL (уровень 50) – Критическая ошибка, возможно завершение программы
# parser_logger.critical("КРИТИЧЕСКАЯ ОШИБКА: Отказ системы!")
#
# # 6️⃣ EXCEPTION (уровень 40, но с traceback) – Логирует ошибку с полным traceback
# try:
#     1 / 0  # Деление на ноль вызовет исключение
# except Exception as e:
#     parser_logger.exception("Исключение: Ошибка деления на ноль")
