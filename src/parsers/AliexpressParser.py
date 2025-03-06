import json
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from tqdm import tqdm
from src.parsers.AbstractParser import AbstractParser

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
            
            # Locate the search input field and enter the query
            search_input = self.driver.find_element(By.CSS_SELECTOR, '[class="RedSearchBar_RedSearchBar__input__7hkcj"]')
            search_input.send_keys(self.request)
            
            # Locate and click the search button
            search_button = self.driver.find_element(By.CSS_SELECTOR, '[class="RedSearchBar_RedSearchBar__submit__7hkcj"]')
            search_button.click()
            
            parser_logger.info(f"{self.__class__.__name__}: Search for query '{self.request}' completed successfully")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Error while entering search query '{self.request}': {e}")

    def _pars_page(self):
        """Parses product cards on the AliExpress search results page."""
        from src.logger.logger import parser_logger
        parser_logger.info(f"{self.__class__.__name__}: Starting page parsing")
        
        self.new_data = []
        try:
            # Locate all product cards
            product_cards = self.driver.find_elements(By.CSS_SELECTOR, 'red-snippet_RedSnippet__mainBlock__e15tmk')
            parser_logger.info(f"{self.__class__.__name__}: Found {len(product_cards)} product cards")
        except Exception as e:
            parser_logger.exception(f"{self.__class__.__name__}: Error locating product cards: {e}")
            product_cards = []
        
        for card in tqdm(product_cards, desc="Parsing Products", unit="product"):
            try:
                # Extract product details
                description = card.find_element(By.CLASS_NAME, 'red-snippet_RedSnippet__title__e15tmk red-typography-utils_style__body_s_regular_16__1f5x18').text.strip()
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
            
            try:
                product_id = card.find_element(By.CSS_SELECTOR, 'div.red-snippet_RedSnippet__container__e15tmk').get_attribute('data-product-id')
            except Exception:
                product_id = 'Product ID not found'
            
            # Store extracted data
            data = {
                'description': description,
                'url': url,
                'price': price,
                'product_id': product_id
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
            self._setup()
            parser_logger.info(f"{self.__class__.__name__}: WebDriver successfully configured")
            
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