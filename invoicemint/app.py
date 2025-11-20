import customtkinter as ctk
from invoicemint.ui.main_ui import MainApp

def main():
    ctk.set_appearance_mode("System")   # "Light", "Dark", or "System"
    ctk.set_default_color_theme("blue") # "blue", "green", "dark-blue"
    app = MainApp()
    app.mainloop()

if __name__ == "__main__":
    main()