import json
import os
import sys

from pandas.core.roperator import rtruediv
from tqdm import tqdm
from time import sleep
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.parsers.AbstractParser import AbstractParser
from src.parsers.AbstractParser import Loading_Source_Data

class ETMParser(AbstractParser):

    def _run_once(self):
        """Создаёт JSON-файл с данными, если метод вызывается впервые."""
        from src.logger.logger import parser_logger
        try:
            if self._is_first_instance():
                parser_logger.info(f"{self.__class__.__name__}: Первый вызов _run_once(), создаём JSON-файл")

                # Получение текущей даты и времени
                current_time = datetime.now().strftime("%H-%M-%S_%d-%m-%Y")

                # Формирование пути для файла
                directory = "./data/JSON/ETMData"
                filename = f"ETMData_{current_time}.json"
                AbstractParser._filepath = os.path.join(directory, filename)
                parser_logger.debug(
                    f"{self.__class__.__name__}: JSON-файл будет сохранён по пути: {AbstractParser._filepath}")

                # Создание директории, если её нет
                os.makedirs(directory, exist_ok=True)
                parser_logger.info(f"{self.__class__.__name__}: Директория проверена/создана: {directory}")

                # Формирование данных для записи в JSON
                metadata = {
                    "Дата и время создания файла": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Данные": self.data  # Если `self.data` пустой, сохраняется пустой объект
                }

                # Запись данных в файл
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
        """Вводит запрос в строку поиска и нажимает необходимые кнопки на сайте."""
        from src.logger.logger import parser_logger
        try:
            parser_logger.info(f"{self.__class__.__name__}: Начало ввода запроса '{self.request}'")

            # Ввод поискового запроса
            try:
                search_input = self.driver.find_element(By.CSS_SELECTOR,
                                                        '[class="MuiInputBase-input MuiOutlinedInput-input MuiInputBase-inputAdornedStart MuiInputBase-inputAdornedEnd mui-style-17dpdqx"]') 
                search_input.send_keys(self.request)
                parser_logger.info(f"{self.__class__.__name__}: Запрос '{self.request}' введён")
            except Exception:
                parser_logger.warning(f"{self.__class__.__name__}: Поле ввода запроса не найдено")

            self.driver.implicitly_wait(2)  # Установка неявного ожидания

            # Нажатие кнопки "Ваш город -> ДА"
            try: 
                confirm_city_button = self.driver.find_element(By.CSS_SELECTOR,
                                                               '[data-testid="okay-button"]')
                confirm_city_button.click()
                parser_logger.info(f"{self.__class__.__name__}: Кнопка 'Ваш город -> ДА' нажата")
            except Exception:
                parser_logger.warning(f"{self.__class__.__name__}: Кнопка 'Ваш город -> ДА' не найдена")

            # Нажатие кнопки "Использовать куки -> Ок"
            try:
                cookie_button = self.driver.find_element(By.CSS_SELECTOR,
                                                         '[data-testid="understand-button"]')
                cookie_button.click()
                parser_logger.info(f"{self.__class__.__name__}: Кнопка 'Использовать куки -> Ок' нажата")
            except Exception:
                parser_logger.warning(f"{self.__class__.__name__}: Кнопка 'Использовать куки -> Ок' не найдена")

            # Нажатие кнопки "Найти"
            try:
                search_button = self.driver.find_element(By.CSS_SELECTOR,
                                                         '[data-testid="catalog-search-button-adaptive"]')
                search_button.click()
                parser_logger.info(f"{self.__class__.__name__}: Кнопка 'Найти' нажата")
            except Exception:
                parser_logger.warning(f"{self.__class__.__name__}: Кнопка 'Найти' не найдена")

        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка на этапе ввода запроса '{self.request}': {e}")

    def _pars_page(self):
        """Парсит товары на странице и сохраняет данные."""
        from src.logger.logger import parser_logger
        try:
            parser_logger.info(f"{self.__class__.__name__}: Начало парсинга страницы")

            self.new_data = []
            max_scrolls = 10  # Ограничение на количество прокруток
            scroll_count = 0

            # Уменьшаем масштаб страницы для захвата большего количества товаров
            self.driver.execute_script("document.body.style.zoom='0.25';")
            parser_logger.debug(
                f"{self.__class__.__name__}: Масштаб страницы уменьшен для отображения большего количества карточек")

            first_cycle = True
            previous_product_code = ''

            #while scroll_count < max_scrolls:
            try:
                titles = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, '[class="tss-o60ib4-grid_item"]'))
                )
                parser_logger.info(f"{self.__class__.__name__}: Найдено {len(titles)} карточек товаров")
            except Exception as e:
                parser_logger.exception(f"{self.__class__.__name__}: Ошибка поиска карточек товара: {e}")
                #break

            for title in titles:
                try:
                    try:
                        description = title.find_element(By.CSS_SELECTOR,
                                                            '[class="MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineHover tss-lrg5ji-root-blue-title mui-style-i8aqv9"]').get_attribute(
                            'innerText')
                    except Exception:
                        description = 'Описание не найдено'
                        parser_logger.warning(f"{self.__class__.__name__}: Описание товара не найдено")

                    try:
                        url = title.find_element(By.CSS_SELECTOR,
                                                    'a.MuiTypography-root.MuiTypography-inherit.MuiLink-root.MuiLink-underlineHover').get_attribute(
                            'href')
                    except Exception:
                        url = 'Ссылка не найдена'
                        parser_logger.warning(f"{self.__class__.__name__}: Ссылка на товар не найдена")

                    try:
                        price = WebDriverWait(title, 5).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, '[class="MuiTypography-root MuiTypography-title4 tss-1mz6fdu-priceColor-priceCount mui-style-1rtbk0o"]'))
                        ).text.replace(' ₽/шт', '').replace(' ', '')
                    except Exception:
                        price = 'Цена не найдена'
                        parser_logger.warning(f"{self.__class__.__name__}: Цена товара не найдена")

                    try:
                        product_code = title.find_element(By.CSS_SELECTOR,
                                                            '[class="tss-ao7i46-text MuiBox-root mui-style-0"]').text
                    except Exception:
                        product_code = 'Код продукта не найден'
                        parser_logger.warning(f"{self.__class__.__name__}: Код продукта не найден")

                    try:
                        article = title.find_element(By.CSS_SELECTOR, '[class="tss-9cdrin-good_descr_value"]').text
                    except Exception:
                        article = 'Артикул не найден'
                        parser_logger.warning(f"{self.__class__.__name__}: Артикул не найден")

                    data = {
                        'description': description,
                        'url': url,
                        'price': price,
                        'product_code': product_code,
                        'article': article
                    }

                    #if first_cycle:
                    self.new_data.append(data)
                    parser_logger.debug(f"{self.__class__.__name__}: Добавлена карточка товара: {data}")
                        # Для прокрутки страницы вниз
                        # target_testid = "catalog-list-item-1"
                        # --- Используем CSS Selector (Рекомендуется) ---
                        # stable_selector = f"[data-testid='{target_testid}']"
                        # selector_tuple = (By.CSS_SELECTOR, stable_selector)
                        # element_present = WebDriverWait(self.driver, 10).until(
                        #     EC.presence_of_element_located(selector_tuple)
                        # )
                        # js_script = "return arguments[0] ? arguments[0].offsetHeight : null;"
                        # card_height = self.driver.execute_script(js_script, element_present)
                        
                        # if card_height is not None:
                        #     print(f"Высота элемента с {target_testid}: {card_height}")
                        # else:
                        #     print("Не удалось получить высоту: JS вернул null (хотя элемент был найден).")
                    #else:
                    #    if previous_product_code != product_code:
                    #        self.new_data.append(data)
                    #        parser_logger.debug(
                    #            f"{self.__class__.__name__}: Добавлена новая карточка товара: {data}")

                except Exception as e:
                    parser_logger.exception(f"{self.__class__.__name__}: Ошибка парсинга карточек товара: {e}")
                    continue

            # try:
            #     self.driver.execute_script(f"window.scrollBy(0, {card_height});")
            #     parser_logger.debug(f"{self.__class__.__name__}: Прокрутка страницы вниз (шаг {scroll_count + 1})")

            #     sleep(1)  # Пауза для подгрузки контента
            #     scroll_count += 1

            # except Exception as e:
            #     parser_logger.exception(f"{self.__class__.__name__}: Ошибка прокрутки страницы: {e}")
            #     break

            previous_product_code = product_code
            first_cycle = False

            parser_logger.info(f"{self.__class__.__name__}: Парсинг завершён, обработано {len(self.new_data)} карточек")

        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка при парсинге страницы: {e}")

    def parse(self):
        """Запускает полный цикл парсинга данных."""
        from src.logger.logger import parser_logger
        try:
            parser_logger.info(f"{self.__class__.__name__}: Начало парсинга")

            self._setup()
            parser_logger.info(f"{self.__class__.__name__}: WebDriver успешно настроен")

            self._get_url()
            parser_logger.info(f"{self.__class__.__name__}: Загружен сайт {self.url}")

            self._entering_request()
            parser_logger.info(f"{self.__class__.__name__}: Поисковый запрос '{self.request}' отправлен")

            self._load_data()
            parser_logger.info(f"{self.__class__.__name__}: Загружены предыдущие данные (если есть)")

            self._pars_page()
            parser_logger.info(
                f"{self.__class__.__name__}: Парсинг страницы завершён, найдено {len(self.new_data)} товаров")

            self._add_request()
            parser_logger.info(f"{self.__class__.__name__}: Новые данные добавлены в JSON")

            self._save_data()
            parser_logger.info(f"{self.__class__.__name__}: Данные успешно сохранены")

            parser_logger.info(f"{self.__class__.__name__}: Парсинг завершён, обработано {len(self.data)} товаров")

        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка во время парсинга: {e}")
