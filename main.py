import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import io
import os
from dotenv import load_dotenv

# ========== CONFIGURATION OF API ==========

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")
if not API_KEY:
    raise ValueError(
        "No API key found. Please set WEATHER_API_KEY in your .env file.")

BASE_URL = "http://api.weatherapi.com/v1"

# ========== WEATHER APP CLASS ==========


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌦️ Weather Pro")
        self.geometry("420x540")
        self.resizable(False, False)
        self.configure(bg="#232946")
        self.iconbitmap("")  # Optional: Set a custom icon

        # Track temperature unit (Celsius/Fahrenheit)
        self.use_celsius = tk.BooleanVar(value=True)

        # --- UI Elements ---
        self.create_widgets()

    def create_widgets(self):
        # App Title
        title = tk.Label(self, text="Weather Pro", font=(
            "Montserrat", 22, "bold"), fg="#eebbc3", bg="#232946")
        title.pack(pady=10)

        # City Entry
        city_frame = tk.Frame(self, bg="#232946")
        city_frame.pack(pady=10)
        self.city_entry = ttk.Entry(
            city_frame, font=("Segoe UI", 14), width=20)
        self.city_entry.pack(side=tk.LEFT, padx=5)
        self.city_entry.bind("<Return>", lambda e: self.get_weather())
        search_btn = ttk.Button(
            city_frame, text="Search", command=self.get_weather)
        search_btn.pack(side=tk.LEFT)

        # Temperature Unit Switch
        unit_switch = ttk.Checkbutton(
            self, text="Show °F", variable=self.use_celsius, onvalue=False,
            offvalue=True,
            command=self.update_unit, style="Switch.TCheckbutton"
        )
        unit_switch.pack(pady=5)

        # Weather Display Area
        self.weather_frame = tk.Frame(
            self, bg="#393e46", bd=2, relief="groove")
        self.weather_frame.pack(pady=15, fill=tk.X, padx=25)

        # Weather Icon
        self.icon_label = tk.Label(self.weather_frame, bg="#393e46")
        self.icon_label.pack(pady=8)

        # Weather Info
        self.info_label = tk.Label(self.weather_frame, text="", font=(
            "Segoe UI", 13), fg="#eebbc3", bg="#393e46", justify=tk.LEFT)
        self.info_label.pack(pady=5)

        # Forecast Toggle Button
        self.show_forecast = tk.BooleanVar(value=False)
        forecast_btn = ttk.Checkbutton(
            self, text="Show 3-Day Forecast", variable=self.show_forecast,
            command=self.toggle_forecast
        )
        forecast_btn.pack(pady=8)

        # Forecast Display
        self.forecast_frame = tk.Frame(self, bg="#393e46")
        self.forecast_frame.pack(pady=5, fill=tk.X, padx=25)
        self.forecast_frame.pack_forget()  # Hide initially

        # Status Label
        self.status_label = tk.Label(self, text="", font=(
            "Segoe UI", 10), fg="#eebbc3", bg="#232946")
        self.status_label.pack(pady=6)

    def update_unit(self):
        # Refresh weather info with new unit
        if hasattr(self, "last_city"):
            self.get_weather(city=self.last_city)

    def toggle_forecast(self):
        # Show/hide forecast frame
        if self.show_forecast.get():
            self.forecast_frame.pack(pady=5, fill=tk.X, padx=25)
        else:
            self.forecast_frame.pack_forget()
        # Refresh if city is present
        if hasattr(self, "last_city"):
            self.get_weather(city=self.last_city)

    def get_weather(self, city=None):
        # Get weather data for the given city
        city = city or self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            return
        self.last_city = city
        self.status_label.config(text="Loading weather data...")

        try:
            # --- Current Weather ---
            params = {
                "key": API_KEY,
                "q": city,
                "aqi": "no"
            }
            url = f"{BASE_URL}/current.json"
            resp = requests.get(url, params=params, timeout=8)
            data = resp.json()

            if "error" in data:
                raise Exception(data["error"]["message"])

            # --- Display Weather Info ---
            self.display_weather(data)

            # --- Forecast (if enabled) ---
            if self.show_forecast.get():
                self.get_forecast(city)
            else:
                self.clear_forecast()

            self.status_label.config(text="")

        except Exception as e:
            self.status_label.config(text="")
            messagebox.showerror("Weather Error", str(e))
            self.clear_weather()
            self.clear_forecast()

    def display_weather(self, data):
        # Extract data
        location = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = data["current"]["temp_c"]
        temp_f = data["current"]["temp_f"]
        condition = data["current"]["condition"]["text"]
        icon_url = "http:" + data["current"]["condition"]["icon"]
        humidity = data["current"]["humidity"]
        wind_kph = data["current"]["wind_kph"]
        wind_mph = data["current"]["wind_mph"]

        # Download and display weather icon
        try:
            icon_img = Image.open(io.BytesIO(
                requests.get(icon_url).content)).resize((60, 60))
            icon_img = ImageTk.PhotoImage(icon_img)
            self.icon_label.config(image=icon_img)
            self.icon_label.image = icon_img
        except Exception:
            self.icon_label.config(image="")

        # Temperature unit
        if self.use_celsius.get():
            temp = f"{temp_c}°C"
            wind = f"{wind_kph} km/h"
        else:
            temp = f"{temp_f}°F"
            wind = f"{wind_mph} mph"

        # Display info
        info = (
            f"📍 {location}, {country}\n"
            f"🌡 Temperature: {temp}\n"
            f"🌤 Condition: {condition}\n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬 Wind: {wind}"
        )
        self.info_label.config(text=info)

    def clear_weather(self):
        self.icon_label.config(image="")
        self.info_label.config(text="")

    def get_forecast(self, city):
        # Fetch and display 3-day forecast
        try:
            params = {
                "key": API_KEY,
                "q": city,
                "days": 3,
                "aqi": "no",
                "alerts": "no"
            }
            url = f"{BASE_URL}/forecast.json"
            resp = requests.get(url, params=params, timeout=8)
            data = resp.json()
            if "error" in data:
                raise Exception(data["error"]["message"])

            # Clear previous
            for widget in self.forecast_frame.winfo_children():
                widget.destroy()

            # Display forecast
            for day in data["forecast"]["forecastday"]:
                date = day["date"]
                avg_c = day["day"]["avgtemp_c"]
                avg_f = day["day"]["avgtemp_f"]
                cond = day["day"]["condition"]["text"]
                icon_url = "http:" + day["day"]["condition"]["icon"]

                # Icon
                try:
                    icon_img = Image.open(io.BytesIO(
                        requests.get(icon_url).content)).resize((38, 38))
                    icon_img = ImageTk.PhotoImage(icon_img)
                except Exception:
                    icon_img = None

                # Frame for each day
                f = tk.Frame(self.forecast_frame, bg="#393e46")
                f.pack(fill=tk.X, pady=2)
                if icon_img:
                    lbl_icon = tk.Label(f, image=icon_img, bg="#393e46")
                    lbl_icon.image = icon_img
                    lbl_icon.pack(side=tk.LEFT, padx=5)
                temp = f"{avg_c}°C" if self.use_celsius.get() else f"{avg_f}°F"
                lbl = tk.Label(
                    f, text=f"{date}: {cond}, {temp}",
                    font=("Segoe UI", 11), fg="#eebbc3", bg="#393e46"
                )
                lbl.pack(side=tk.LEFT, padx=4)
        except Exception as e:
            messagebox.showerror("Forecast Error", str(e))
            self.clear_forecast()

    def clear_forecast(self):
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

# ========== CUSTOM STYLE ==========


def set_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TEntry", foreground="#232946", font=("Segoe UI", 13))
    style.configure("TButton", font=("Segoe UI", 12, "bold"),
                    foreground="#232946", background="#eebbc3")
    style.configure("TCheckbutton", background="#232946",
                    foreground="#eebbc3", font=("Segoe UI", 11))
    style.map("TButton", background=[("active", "#eebbc3")])
    style.configure("Switch.TCheckbutton", background="#232946",
                    foreground="#eebbc3", font=("Segoe UI", 11, "italic"))


# ========== MAIN ==========
if __name__ == "__main__":
    set_style()
    app = WeatherApp()
    app.mainloop()
