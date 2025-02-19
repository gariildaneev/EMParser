import json
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from tqdm import tqdm
from src.parsers.AbstractParser import AbstractParser



class BonpetParser(AbstractParser):
    def _run_once(self):
        """Создаёт JSON-файл с данными, если метод вызывается впервые."""
        from src.logger.logger import parser_logger
        try:
            if self._is_first_instance():
                parser_logger.info(f"{self.__class__.__name__}: Первый вызов _run_once(), создаём файл JSON")
                # Получение текущей даты и времени
                current_time = datetime.now().strftime("%H-%M-%S_%d-%m-%Y")
                # Формирование пути для файла
                directory = "./data/JSON/BonpetData"
                filename = f"BonpetData_{current_time}.json"
                AbstractParser._filepath = os.path.join(directory, filename)
                parser_logger.debug(
                    f"{self.__class__.__name__}: JSON-файл будет сохранён по пути: {AbstractParser._filepath}")
                # Создание директории, если она не существует
                os.makedirs(directory, exist_ok=True)
                parser_logger.info(f"{self.__class__.__name__}: Директория проверена/создана: {directory}")
                # Формирование данных для записи в JSON
                metadata = {
                    "Дата и время создания файла": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Данные": self.data  # Если `self.data` пустой, сохраняется пустой объект
                }
                # Запись данных в файл в формате JSON
                with open(AbstractParser._filepath, 'w', encoding='utf-8') as file:
                    json.dump(metadata, file, ensure_ascii=False, indent=4)
                parser_logger.info(
                    f"{self.__class__.__name__}: Файл {filename} успешно создан, записано {len(self.data)} записей")
            else:
                parser_logger.warning(
                    f"{self.__class__.__name__}: Метод _run_once() уже был вызван ранее, повторный запуск игнорируется")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка при выполнении _run_once(): {e}")

    def _entering_request(self):
        """Вводит запрос в строку поиска и нажимает кнопку поиска на Bonpet.tech."""
        from src.logger.logger import parser_logger
        try:
            parser_logger.info(f"{self.__class__.__name__}: Ввод запроса '{self.request}' в поисковую строку")
            # Находим поле ввода и вводим запрос
            search_input = self.driver.find_element(By.CSS_SELECTOR, '[class="form-control"]')  # Update selector
            search_input.send_keys(self.request)
            # Нажимаем кнопку поиска
            search_button = self.driver.find_element(By.CSS_SELECTOR, '[class="button-search"]')  # Update selector
            search_button.click()
            parser_logger.info(f"{self.__class__.__name__}: Поиск по запросу '{self.request}' успешно выполнен")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка на этапе ввода запроса '{self.request}': {e}")

    def _pars_page(self):
        """Парсит товары на странице Bonpet.tech и сохраняет данные."""
        from src.logger.logger import parser_logger
        parser_logger.info(f"{self.__class__.__name__}: Начало парсинга страницы")
        self.new_data = []
        try:
            # Поиск карточек товаров
            titles = self.driver.find_elements(By.CSS_SELECTOR, '[class="product-item"]')  # Update selector
            parser_logger.info(f"{self.__class__.__name__}: Найдено {len(titles)} карточек товаров")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка поиска карточек товара: {e}")
            titles = []
        for title in titles:
            try:
                description = title.find_element(By.CSS_SELECTOR, '[class="name textS tight pt-2"]').get_attribute('innerText')
            except Exception:
                description = 'Описание не найдено'
            try:
                url = title.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except Exception:
                url = 'Ссылка не найдена'
            try:
                price = title.find_element(By.CSS_SELECTOR, '[class="price"]').get_attribute('innerText')
                #price = price.replace("\u00A0", "").split()[0]
            except Exception:
                price = 'Цена не найдена'
            try:
                cards_ID = title.get_attribute('id')
            except Exception:
                cards_ID = 'Код продукта не найден'
            data = {
                'description': description,
                'url': url,
                'price': price,
                'cards_ID': cards_ID
            }

            # Log the extracted data for debugging
            parser_logger.debug(f"{self.__class__.__name__}: Извлечённые данные для карточки: {data}")

            self.new_data.append(data)
        parser_logger.info(
            f"{self.__class__.__name__}: Парсинг завершён, добавлено {len(self.new_data)} карточек в JSON")

    def parse(self):
        """Запускает полный цикл парсинга Bonpet.tech."""
        from src.logger.logger import parser_logger
        parser_logger.info(f"{self.__class__.__name__}: Начало парсинга Bonpet.tech для запроса '{self.request}'")
        try:
            self._setup()
            parser_logger.info(f"{self.__class__.__name__}: WebDriver успешно настроен")
            self._get_url()
            parser_logger.info(f"{self.__class__.__name__}: Страница Bonpet.tech успешно загружена")
            self._entering_request()
            parser_logger.info(f"{self.__class__.__name__}: Запрос '{self.request}' отправлен")
            self._load_data()
            parser_logger.info(f"{self.__class__.__name__}: Загружены предыдущие данные (если есть)")
            self._pars_page()
            parser_logger.info(
                f"{self.__class__.__name__}: Парсинг страницы завершён, найдено {len(self.new_data)} товаров")
            self._add_request()
            parser_logger.info(f"{self.__class__.__name__}: Новые данные добавлены в JSON")
            self._save_data()
            parser_logger.info(f"{self.__class__.__name__}: Данные успешно сохранены")
            parser_logger.info(
                f"{self.__class__.__name__}: Парсинг завершён, всего обработано {len(self.data)} товаров")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка во время парсинга: {e}")