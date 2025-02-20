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
from src.utils.ExcelSaver import ExcelSaver
from src.parsers.AbstractParser import Loading_Source_Data
import time

# Initialize CustomTkinter
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class ParserApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Shops Parser")
        self.geometry("800x600")

        # Variables
        self.selected_shops = []
        self.original_file_path = Path(__file__).parent / "data.xlsx"  # Original file
        self.temp_file_path = Path(__file__).parent / "temp_data.xlsx"  # Temporary file
        self.workbook = None  # To store the loaded workbook

        # Create a temporary copy of the original file at startup
        self.create_temp_copy()

        # Layout
        self.create_widgets()

    def create_temp_copy(self):
        """Create a temporary copy of the original Excel file."""
        if self.original_file_path.exists():
            shutil.copy(self.original_file_path, self.temp_file_path)
            self.after(100, lambda: self.log_to_console("Created temporary copy of the original file."))
        else:
            self.after(100, lambda: self.log_to_console("Error: Original Excel file not found."))

    def create_widgets(self):
        # Title Label
        title_label = ctk.CTkLabel(self, text="Shops Parser", font=("Arial", 20, "bold"))
        title_label.pack(pady=10)

        # Shop Selection Frame
        shop_frame = ctk.CTkFrame(self)
        shop_frame.pack(pady=10, padx=20, fill="x")

        # Checkboxes for Shops
        shops = ["ChipDip", "eBay", "ETM", "YandexMarket", "Bonpet.tech"]

        self.shop_map = {
            "ChipDip": {"id": 1, "site_name": "https://www.chipdip.ru/", "json_folder": "data/JSON/ChipDipData"},
            "eBay": {"id": 2, "site_name": "https://www.ebay.com/", "json_folder": "data/JSON/eBayData"},
            "ETM": {"id": 3, "site_name": "https://www.etm.ru/", "json_folder": "data/JSON/ETMData"},
            "YandexMarket": {"id": 4, "site_name": "https://market.yandex.ru/", "json_folder": "data/JSON/YandexMarketData"},
            "Bonpet.tech": {"id": 5, "site_name": "https://bonpet.tech/", "json_folder": "data/JSON/BonpetData"}
        }
        for shop in shops:
            checkbox = ctk.CTkCheckBox(shop_frame, text=shop, command=lambda s=shop: self.toggle_shop(s))
            checkbox.pack(side="left", padx=10)
            self.selected_shops.append(checkbox)

        # Excel File Buttons
        excel_frame = ctk.CTkFrame(self)
        excel_frame.pack(pady=10, padx=20, fill="x")

        open_excel_button = ctk.CTkButton(excel_frame, text="Открыть .xlsx файл ", command=self.open_excel)
        open_excel_button.pack(side="left", padx=10)

        download_results_button = ctk.CTkButton(excel_frame, text="Скачать результаты", command=self.download_results)
        download_results_button.pack(side="left", padx=10)

        # Console Output
        console_frame = ctk.CTkFrame(self)
        console_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.console_output = ctk.CTkTextbox(console_frame, height=150, state="disabled")
        self.console_output.pack(fill="both", expand=True)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")

        # Action Buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(pady=10, padx=20, fill="x")

        start_parsing_button = ctk.CTkButton(action_frame, text="Начать парсинг", command=self.start_parsing)
        start_parsing_button.pack(side="left", padx=10)

    def toggle_shop(self, shop_name):
        print(f"{shop_name} toggled")

    def open_excel(self):
        try:
            # Open the temporary file in the default application (e.g., MS Excel)
            if self.temp_file_path.exists():
                if platform.system() == "Windows":
                    os.startfile(self.temp_file_path)  # For Windows
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open {self.temp_file_path}")
                else:  # Linux
                    os.system(f"xdg-open {self.temp_file_path}")

                # Reload the workbook from the temporary file
                self.reload_workbook()
                self.log_to_console(f"Opened Excel file: {self.temp_file_path}")
            else:
                self.log_to_console("Error: Temporary Excel file not found.")
        except Exception as e:
            self.log_to_console(f"Error opening Excel file: {e}")

    def reload_workbook(self):
        """Reload the workbook from the temporary file."""
        try:
            self.workbook = openpyxl.load_workbook(self.temp_file_path)
            self.log_to_console("Reloaded workbook from the temporary file.")
        except Exception as e:
            self.log_to_console(f"Error reloading workbook: {e}")

    def download_results(self):
        try:
            # Reload the workbook to ensure it reflects the latest changes
            self.reload_workbook()

            # Save the updated Excel file to the Downloads folder
            downloads_folder = Path.home() / "Downloads"
            results_file_path = downloads_folder / "results.xlsx"

            if self.workbook:
                # Save the workbook to the temporary file first
                self.workbook.save(self.temp_file_path)
                # Then copy it to the Downloads folder
                shutil.copy(self.temp_file_path, results_file_path)
                self.log_to_console(f"Results downloaded to: {results_file_path}")
            else:
                self.log_to_console("Error: No workbook loaded to download.")
        except Exception as e:
            self.log_to_console(f"Error downloading results: {e}")

    def start_parsing(self):
        # Start parsing in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_parsers).start()

    def run_parsers(self):
        """Run selected parsers with a progress bar."""
        selected_shops = [cb.cget("text") for cb in self.selected_shops if cb.get() == 1]
        if not selected_shops:
            self.log_to_console("No parsers selected.")
            return

        self.log_to_console(f"Selected parsers: {', '.join(selected_shops)}")
        
        # Show progress bar
        self.progress_bar.set(0)  # Reset progress
        self.progress_bar.pack(pady=10, padx=20, fill="x")  # Show progress bar
        
        for shop in selected_shops:
            shop_info = self.shop_map.get(shop)
            if not shop_info:
                self.log_to_console(f"Unknown shop: {shop}")
                continue

            site_name = shop_info["site_name"]
            json_folder = shop_info["json_folder"]
            parser_class = {
                "Bonpet.tech": BonpetParser
            }.get(shop)

            if not parser_class:
                self.log_to_console(f"No parser class found for shop: {shop}")
                continue

            self.log_to_console(f"Starting parser for: {site_name}")
            try:
                self.progress_bar.set(0)  # Reset progress
                articles = list(Loading_Source_Data('data.xlsx').loading_articles())
                self.log_to_console(f"Loaded {len(articles)} articles for parsing.")

                self.smooth_progress_to(0.05)

                total_articles = len(articles)
                if total_articles > 0:
                    step = 0.8 / total_articles  # Step size for progress

                for index, article in enumerate(articles):
                    try:
                        parser = parser_class(url=site_name, request=article, items=[article])
                        parser.parse()

                        self.log_to_console(f"Successfully parsed article: {article}")

                        # Update progress bar
                        progress_value = 0.05 + (index + 1) * step  # Normalize progress
                        self.smooth_progress_to(progress_value)

                    except Exception as e:
                        self.log_to_console(f"Error parsing article {article}: {e}")

                saver = ExcelSaver(json_folder=json_folder)
                saver.process_data()
                self.log_to_console(f"Saved parsed data to JSON folder: {json_folder}")
                self.smooth_progress_to(0.90)
            except Exception as e:
                self.log_to_console(f"Error parsing shop {shop}: {e}")

        try:
            saver_aggregate = ExcelSaver()
            saver_aggregate.aggregate_prices_to_first_sheet()
            self.log_to_console("All data successfully aggregated into Excel.")
            self.smooth_progress_to(1.0)
            
        except Exception as e:
            self.log_to_console(f"Error aggregating data into Excel: {e}")

        # Gradually fade out progress bar
        self.fade_out_progress_bar()

    def fade_out_progress_bar(self):
        """Gradually fade out the progress bar."""
        for i in range(20, -1, -1):
            self.progress_bar.configure(progress_color=f"gray{i}")  # Adjust color for fading effect
            self.update_idletasks()
            time.sleep(0.05)
        
        self.progress_bar.pack_forget()  # Hide after fading
    
    def smooth_progress_to(self, target_value, duration=0.3):
        """Smoothly animate the progress bar to a target value."""
        current_value = self.progress_bar.get()
        steps = 20  # Number of small steps for smoothness
        step_size = (target_value - current_value) / steps

        for _ in range(steps):
            current_value += step_size
            self.progress_bar.set(current_value)
            self.update_idletasks()
            time.sleep(duration / steps)  # Small delay for smooth effect


    def log_to_console(self, message):
        """Log a message to the console output."""
        if hasattr(self, "console_output"):  # Ensure the console widget exists
            self.console_output.configure(state="normal")
            self.console_output.insert("end", message + "\n")
            self.console_output.configure(state="disabled")
            self.console_output.see("end")
        else:
            print(f"Console not initialized yet: {message}")


if __name__ == "__main__":
    app = ParserApp()
    app.mainloop()