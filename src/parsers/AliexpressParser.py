import json
import os
import random
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from src.parsers.AbstractParser import AbstractParser
from selenium.webdriver.common.action_chains import ActionChains

class AliexpressParser(AbstractParser):

    def _run_once(self):
        """Creates a JSON file with initial data if this is the first instance."""
        from src.logger.logger import parser_logger
        try:
            if self._is_first_instance():
                parser_logger.info(f"{self.__class__.__name__}: First run of _run_once(), creating JSON file")
                
                # Generate timestamped filename
                current_time = datetime.now().strftime("%H-%M-%S_%d-%m-%Y")
                directory = "./data/JSON/AliexpressData"
                filename = f"AliexpressData_{current_time}.json"
                AbstractParser._filepath = os.path.join(directory, filename)
                
                # Ensure directory exists
                os.makedirs(directory, exist_ok=True)
                parser_logger.debug(f"{self.__class__.__name__}: Directory checked/created: {directory}")
                
                # Prepare metadata
                metadata = {
                    "Creation Date and Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "Data": self.data  # If `self.data` is empty, it will save an empty object
                }
                
                # Write to JSON file
                with open(AbstractParser._filepath, 'w', encoding='utf-8') as file:
                    json.dump(metadata, file, ensure_ascii=False, indent=4)
                
                parser_logger.info(
                    f"{self.__class__.__name__}: File {filename} successfully created, saved {len(self.data)} records")
            else:
                parser_logger.warning(
                    f"{self.__class__.__name__}: _run_once() has already been called, skipping duplicate execution")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Error during _run_once(): {e}")

    def _entering_request(self):
        """Enters the search query on AliExpress and initiates the search."""
        from src.logger.logger import parser_logger
        try:
            parser_logger.info(f"{self.__class__.__name__}: Entering search query '{self.request}'")
            
            # Нажатие кнопки *какой-то город* - Верно
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                                                    '[class="ShipToHeaderItem_ButtonCTA__button__17o6s ShipToHeaderItem_Button__button__wso54 ShipToHeaderItem_GeoTooltip__mapGeoButton__h6wam"]'))
                )
                self.driver.find_element(By.CSS_SELECTOR,
                                         '[class="ShipToHeaderItem_ButtonCTA__button__17o6s ShipToHeaderItem_Button__button__wso54 ShipToHeaderItem_GeoTooltip__mapGeoButton__h6wam"]').click()
                parser_logger.info(f"{self.__class__.__name__}: Кнопка 'Верно' нажата")
            except Exception:
                parser_logger.warning(f"{self.__class__.__name__}: Кнопка 'Верно' не найдена")

            time.sleep(random.uniform(1.0, 2.0))  # Случайная задержка перед началом ввода

            # Locate the search input field and enter the query
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[class="RedSearchBar_RedSearchBar__input__7hkcj"]'))
            )
            search_input = self.driver.find_element(By.CSS_SELECTOR, '[class="RedSearchBar_RedSearchBar__input__7hkcj"]')
            search_input.clear()  # Очищаем поле ввода перед вводом нового запроса

            for char in self.request:   # Случайная задержка между вводом каждого символа
                search_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            parser_logger.debug(f"{self.__class__.__name__}: Поле ввода поиска найдено")

            

            #ActionChains(self.driver).move_by_offset(20, 45).click().perform()
            time.sleep(random.uniform(1, 3))
        
            
            # Locate and click the search button
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[class="RedSearchBar_RedSearchBar__submit__7hkcj"]'))
            )

            #actions = ActionChains(self.driver)
            #actions.move_by_offset(random.randint(-200, 200), random.randint(-200, 200)).perform()

            search_button.click()
            parser_logger.debug(f"{self.__class__.__name__}: Кнопка поиска найдена и нажата")

            time.sleep(random.uniform(1, 3))
            
            parser_logger.info(f"{self.__class__.__name__}: Search for query '{self.request}' completed successfully")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Error while entering search query '{self.request}': {e}")
            raise  # Повторно выбрасываем исключение, чтобы оно могло быть обработано выше

    def _pars_page(self):
        """Parses product cards on the AliExpress search results page."""
        from src.logger.logger import parser_logger
        parser_logger.info(f"{self.__class__.__name__}: Starting page parsing")
        
        self.new_data = []

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[class="red-snippet_RedSnippet__mainBlock__e15tmk"]'))
            )
            parser_logger.info(f"{self.__class__.__name__}: Найден список товаров")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Ошибка ожидания списка товаров: {e}")
            return

        try:
            # Locate all product cards
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, '[class="red-snippet_RedSnippet__mainBlock__e15tmk"]')
            parser_logger.info(f"{self.__class__.__name__}: Found {len(product_cards)} product cards")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Error locating product cards: {e}")
            product_cards = []
        
        for card in tqdm(product_cards, desc="Parsing Products", unit="product"):
            try:
                # Extract product details
                description = card.find_element(By.CLASS_NAME, 'red-snippet_RedSnippet__title__e15tmk').text.strip()
            except Exception:
                description = 'Description not found'
            
            try:
                url = card.find_element(By.CLASS_NAME, 'red-snippet_RedSnippet__content__e15tmk').get_attribute('href')
            except Exception:
                url = 'URL not found'
            
            try:
                # Locate the parent <div> by its class name
                price_div = card.find_element(By.CLASS_NAME, "red-snippet_RedSnippet__priceNew__e15tmk")
                # Locate the <span> inside the parent <div>
                price = price_div.find_element(By.TAG_NAME, "span").text.strip()
            except Exception:
                price = 'Price not found'
            
            
            # Store extracted data
            data = {
                'description': description,
                'url': url,
                'price': price
            }
            
            # Log extracted data for debugging
            parser_logger.debug(f"{self.__class__.__name__}: Extracted data for product: {data}")
            self.new_data.append(data)
        
        parser_logger.info(
            f"{self.__class__.__name__}: Page parsing completed, added {len(self.new_data)} products to JSON")

    def parse(self):
        """Executes the full parsing cycle for AliExpress."""
        from src.logger.logger import parser_logger
        parser_logger.info(f"{self.__class__.__name__}: Starting AliExpress parsing for query '{self.request}'")
        
        try:
            #self._setup()
            #parser_logger.info(f"{self.__class__.__name__}: WebDriver successfully configured")
            
            self._get_url()
            parser_logger.info(f"{self.__class__.__name__}: AliExpress page successfully loaded")
            
            self._entering_request()
            parser_logger.info(f"{self.__class__.__name__}: Search query '{self.request}' submitted")
            
            self._load_data()
            parser_logger.info(f"{self.__class__.__name__}: Previous data loaded (if available)")
            
            self._pars_page()
            parser_logger.info(
                f"{self.__class__.__name__}: Page parsing completed, found {len(self.new_data)} products")
            
            self._add_request()
            parser_logger.info(f"{self.__class__.__name__}: New data added to JSON")
            
            self._save_data()
            parser_logger.info(f"{self.__class__.__name__}: Data successfully saved")
            
            parser_logger.info(
                f"{self.__class__.__name__}: Parsing completed, processed {len(self.data)} products in total")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Error during parsing: {e}")