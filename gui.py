import customtkinter as ctk
import threading
import openpyxl
from pathlib import Path
import os
import platform
import shutil
import sys
import tqdm
from src.parsers.BonpetParser import BonpetParser
from src.parsers.AliexpressParser import AliexpressParser
from src.parsers.ChipDipParser import ChipDipParser
from src.parsers.ETMParser import ETMParser
from src.parsers.eBayParser import eBayParser
from src.parsers.ZakupkiParser import ZakupkiParser
from src.parsers.YandexMarketParser import YandexMarketParser
from src.utils.ExcelSaver import ExcelSaver
from src.parsers.AbstractParser import Loading_Source_Data

# Initialize CustomTkinter
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class ParserApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shops Parser")
        self.geometry("1000x600")

        # Variables
        self.selected_shops = []
        self.original_file_path = Path(__file__).parent / "data.xlsx"  # Original file for user input
        self.output_file_path = Path(__file__).parent / "output.xlsx"  # Output file for aggregation results
        self.workbook = None  # To store the loaded workbook

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Layout
        self.create_widgets()

    def create_widgets(self):
        # Title Label
        title_label = ctk.CTkLabel(self, text="Shops Parser", font=("Arial", 20, "bold"))
        title_label.pack(pady=10)

        # Shop Selection Frame
        shop_frame = ctk.CTkFrame(self)
        shop_frame.pack(pady=10, padx=20, fill="x")

        # Checkboxes for Shops
        shops = ["ChipDip", "eBay", "ETM", "YandexMarket", "Bonpet.tech", "Aliexpress", "Zakupki"]

        self.shop_map = {
            "ChipDip": {"id": 1, "site_name": "https://www.chipdip.ru/", "json_folder": "data/JSON/ChipDipData"},
            "eBay": {"id": 2, "site_name": "https://www.ebay.com/", "json_folder": "data/JSON/eBayData"},
            "ETM": {"id": 3, "site_name": "https://www.etm.ru/", "json_folder": "data/JSON/ETMData"},
            "YandexMarket": {"id": 4, "site_name": "https://market.yandex.ru/", "json_folder": "data/JSON/YandexMarketData"},
            "Bonpet.tech": {"id": 5, "site_name": "https://bonpet.tech/", "json_folder": "data/JSON/BonpetData"},
            "Aliexpress": {"id": 6, "site_name": "https://aliexpress.ru/", "json_folder": "data/JSON/AliexpressData"},
            "Zakupki": {"id": 7, "site_name": "https://www.zakupki.ru/", "json_folder": "data/JSON/ZakupkiData"},
        }
        for shop in shops:
            checkbox = ctk.CTkCheckBox(shop_frame, text=shop, command=lambda s=shop: self.toggle_shop(s))
            checkbox.pack(side="left", padx=10)
            self.selected_shops.append(checkbox)

        # Excel File Buttons
        excel_frame = ctk.CTkFrame(self)
        excel_frame.pack(pady=10, padx=20, fill="x")

        open_excel_button = ctk.CTkButton(excel_frame, text="Открыть файл с артикулами", command=self.open_excel)
        open_excel_button.pack(side="left", padx=10)

        view_results_button = ctk.CTkButton(excel_frame, text="Посмотреть результат", command=self.view_results)
        view_results_button.pack(side="left", padx=10)

        download_results_button = ctk.CTkButton(excel_frame, text="Скачать результаты", command=self.download_results)
        download_results_button.pack(side="left", padx=10)

        # Console Output
        console_frame = ctk.CTkFrame(self)
        console_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.console_output = ctk.CTkTextbox(console_frame, height=150, state="disabled")
        self.console_output.pack(fill="both", expand=True)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, padx=20, fill="x")

        # Action Buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(pady=10, padx=20, fill="x")

        start_parsing_button = ctk.CTkButton(action_frame, text="Начать парсинг", command=self.start_parsing)
        start_parsing_button.pack(side="left", padx=10)

    def toggle_shop(self, shop_name):
        print(f"{shop_name} toggled")

    def open_excel(self):
        """Open the file containing articles for search."""
        try:
            if self.original_file_path.exists():
                if platform.system() == "Windows":
                    os.startfile(self.original_file_path)  # For Windows
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open {self.original_file_path}")
                else:  # Linux
                    os.system(f"xdg-open {self.original_file_path}")

                self.log_to_console(f"Opened file with articles: {self.original_file_path}")
            else:
                self.log_to_console("Error: File with articles not found.")
        except Exception as e:
            self.log_to_console(f"Error opening file with articles: {e}")

    def view_results(self):
        """Open the file to view aggregated results."""
        try:
            if self.output_file_path.exists():
                if platform.system() == "Windows":
                    os.startfile(self.output_file_path)  # For Windows
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open {self.output_file_path}")
                else:  # Linux
                    os.system(f"xdg-open {self.output_file_path}")

                self.log_to_console(f"Opened results file: {self.output_file_path}")
            else:
                self.log_to_console("Error: Results file not found.")
        except Exception as e:
            self.log_to_console(f"Error opening results file: {e}")

    def download_results(self):
        """Download the aggregated results."""
        try:
            downloads_folder = Path.home() / "Downloads"
            results_file_path = downloads_folder / "results.xlsx"

            # Handle duplicate filenames by appending a number
            counter = 1
            while results_file_path.exists():
                results_file_path = downloads_folder / f"results({counter}).xlsx"
                counter += 1

            if self.output_file_path.exists():
                shutil.copy(self.output_file_path, results_file_path)
                self.log_to_console(f"Results downloaded to: {results_file_path}")
            else:
                self.log_to_console("Error: Results file not found.")
        except Exception as e:
            self.log_to_console(f"Error downloading results: {e}")

    def start_parsing(self):
        # Start parsing in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_parsers).start()

    def run_parsers(self):
        """Run selected parsers."""
        selected_shops = [cb.cget("text") for cb in self.selected_shops if cb.get() == 1]
        if not selected_shops:
            self.log_to_console("No parsers selected.")
            return

        # Define behavior for each shop
        close_browser_behavior = {
            "Aliexpress": False,  
        }

        self.log_to_console(f"Selected parsers: {', '.join(selected_shops)}")
        try:
            # Load articles from data.xlsx
            articles = list(Loading_Source_Data(self.original_file_path).loading_articles())
            self.log_to_console(f"Loaded {len(articles)} articles for parsing.")

            for shop in selected_shops:
                shop_info = self.shop_map.get(shop)
                if not shop_info:
                    self.log_to_console(f"Unknown shop: {shop}")
                    continue

                site_name = shop_info["site_name"]
                json_folder = shop_info["json_folder"]
                parser_class = {
                    "Bonpet.tech": BonpetParser,
                    "Aliexpress": AliexpressParser,
                    "ChipDip": ChipDipParser,
                    "ETM": ETMParser,
                    "eBay": eBayParser,
                    "Zakupki": ZakupkiParser,
                    "YandexMarket": YandexMarketParser
                }.get(shop)

                if not parser_class:
                    self.log_to_console(f"No parser class found for shop: {shop}")
                    continue

                close_browser_after_each_article = close_browser_behavior.get(shop, True)

                self.log_to_console(f"Starting parser for: {site_name} (Close browser after each article: {close_browser_after_each_article})")
                try:
                    # Create a single browser instance for the shop
                    if not close_browser_after_each_article:
                        parser_instance = parser_class(url=site_name, request="", items=[])
                        parser_instance._setup()  # Initialize WebDriver

                    # Parse each article
                    for article in tqdm.tqdm(articles, desc=f"Parsing {site_name}", unit="item"):
                        try:
                            if close_browser_after_each_article:
                                parser_instance = parser_class(url=site_name, request="", items=[])
                            parser_instance.request = article
                            parser_instance.items = [article]
                            parser_instance.parse()
                            self.log_to_console(f"Successfully parsed article: {article}")

                            if close_browser_after_each_article:
                                parser_instance._quit_driver()
                        except Exception as e:
                            self.log_to_console(f"Error parsing article {article}: {e}")

                    # Save parsed data to JSON
                    saver = ExcelSaver(json_folder=json_folder, articles=articles, excel_file=self.output_file_path)
                    saver.process_data()
                    self.log_to_console(f"Saved parsed data to JSON folder: {json_folder}")

                    if not close_browser_after_each_article:
                        parser_instance._quit_driver()

                except Exception as e:
                    self.log_to_console(f"Error parsing shop {shop}: {e}")

            # Aggregate all data into one Excel file
            try:
                saver_aggregate = ExcelSaver(excel_file=self.output_file_path, articles=articles)
                saver_aggregate.aggregate_prices_to_first_sheet()
                self.log_to_console("All data successfully aggregated into Excel.")
            except Exception as e:
                self.log_to_console(f"Error aggregating data into Excel: {e}")

        except Exception as e:
            self.log_to_console(f"Error loading articles: {e}")

    def log_to_console(self, message):
        """Log a message to the console output."""
        if hasattr(self, "console_output"):  # Ensure the console widget exists
            self.console_output.configure(state="normal")
            self.console_output.insert("end", message + "\n")
            self.console_output.configure(state="disabled")
            self.console_output.see("end")
        else:
            print(f"Console not initialized yet: {message}")

    def on_close(self):
        """Handle the application close event."""
        self.destroy()  # Destroy the GUI
        sys.exit(0)  # Ensure the program exits completely


if __name__ == "__main__":
    app = ParserApp()
    app.mainloop()