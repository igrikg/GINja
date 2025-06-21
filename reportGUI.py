import json
from pathlib import Path

import customtkinter as ctk
import tkinter.filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
from PIL import Image
from generator import AnalyserOrso, ReportGenerator, ConfigReport


@dataclass
class FakeEvent:
    width: int
    height: int

def save_config_report(config, filename):
    with open(filename, "w") as f:
        json.dump(asdict(config), f, indent=2)

def load_config_report(cls, filename):
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Config file not found!")
        data = {}
    return cls(**data)


class ReportApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Reflectivity Report Generator")
        self.geometry("1000x600")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("themes/violet.json")
        appearance_mode = ctk.get_appearance_mode()
        self.__bg_color = "#D3CFFC" if appearance_mode == "Dark" else "#EAE8FC"

        self.config_data = load_config_report(ConfigReport,'report_config.json')
        self.inputs = {}
        self.input_file = ''
        self.filename_var = ctk.StringVar(value="No file selected")
        self.auto_update_var = ctk.BooleanVar(value=True)
        # Layout: Left for inputs, Right for plot
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        self.main_area = ctk.CTkFrame(self)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.build_sidebar()
        self.build_plot()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.update_config()
        save_config_report(self.config_data, 'report_config.json')
        self.destroy()

    def get_report(self):
        return ReportGenerator(AnalyserOrso(self.input_file, self.config_data).result)

    def generate_placeholder_figure(self, text="No correct data for report") -> Figure:
        fig = plt.Figure(figsize=(8.27, 11.69))
        ax = fig.add_subplot(111)
        ax.axis('off')
        fig.patch.set_facecolor(self.__bg_color)
        ax.text(
            0.5, 0.5,
            text,
            fontsize=48,
            color='red',
            ha='center',
            va='center',
            rotation=45,
            alpha=0.5,
            transform=ax.transAxes
        )
        return fig

    def generate_report_figure(self) -> Figure:
        try:
            fig = self.get_report().get_figure()
            fig.patch.set_facecolor(self.__bg_color)
            return fig
        except FileNotFoundError:
            return self.generate_placeholder_figure("No such file")
        except Exception as e:
            return self.generate_placeholder_figure(str(e))

    def build_sidebar(self):
        # --- Load and place logo image ---
        logo_image = ctk.CTkImage(
            light_image=Image.open("themes/BNC_logo.png"),
            dark_image=Image.open("themes/BNC_logo.png"),
            size=(150, 56)  # Adjust to fit your sidebar
        )
        logo_label = ctk.CTkLabel(self.sidebar, image=logo_image, text="")
        logo_label.pack(pady=(30, 0))

        ctk.CTkLabel(self.sidebar, text="Report Settings", font=("Arial", 18)).pack(pady=10)
        filename_frame = ctk.CTkFrame(self.sidebar)
        filename_frame.pack(fill="x", pady=5, padx=5)

        self.filename_var = ctk.StringVar(value="No file selected")
        entry = ctk.CTkEntry(filename_frame, textvariable=self.filename_var, state="disabled", width=180)
        entry.pack(side="left", padx=5)

        open_button = ctk.CTkButton(filename_frame, text="Open", width=80, command=self.load_file)
        open_button.pack(side="left", padx=5)

        for field, value in vars(self.config_data).items():
            frame = ctk.CTkFrame(self.sidebar)
            frame.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(frame, text=field, width=100).pack(side="left")
            if isinstance(value, bool):
                var = ctk.BooleanVar(value=value)
                entry = ctk.CTkCheckBox(frame, variable=var, text="", command=self.try_auto_update)
                entry.pack(side="right", padx=10)
            else:
                var = ctk.StringVar(value=str(value))
                entry = ctk.CTkEntry(frame, textvariable=var, width=100)
                entry.pack(side="right",padx=10)
                # Trigger auto update when user leaves the entry field
                entry.bind("<FocusOut>", lambda event: self.try_auto_update())
                entry.bind("<Return>", lambda event: self.try_auto_update())
            self.inputs[field] = var

        self.auto_update_var = ctk.BooleanVar(value=True)
        auto_update = ctk.CTkCheckBox(
            self.sidebar, text="Auto Update", variable=self.auto_update_var
        )
        auto_update.pack(pady=(10, 5))

        button_row = ctk.CTkFrame(self.sidebar)

        button_row.pack(pady=10)

        # Update button
        update_button = ctk.CTkButton(button_row, text="Update", width=80, command=self.update_plot)
        update_button.pack(side="left",padx=5)

        # Save PDF button
        save_button = ctk.CTkButton(button_row, text="Save PDF", width=80, command=self.save_pdf)
        save_button.pack(side="right",padx=5)

    def load_file(self):
        path = tkinter.filedialog.askopenfilename(filetypes=[("ORSO Files", "*.ort")])
        if path:
            self.filename_var.set(Path(path).name)
            self.input_file = path
            if self.auto_update_var.get():
                self.update_plot()

    def try_auto_update(self):
        if self.auto_update_var.get():
            self.update_plot()

    def build_plot(self):
        self.figure = self.generate_report_figure()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.main_area)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()

        # Bind to resize event
        self.main_area.bind("<Configure>", self.lock_a4_ratio)

    def lock_a4_ratio(self, event):
        a4_ratio = 11.69 / 8.27  # ≈ 1.414

        # Use available height
        height_px = event.height*0.95
        width_px = int(height_px / a4_ratio)

        # Reposition and resize canvas
        self.canvas_widget.place(x=(event.width - width_px) // 2,
                                 y=(event.height - height_px) // 2,
                                 width=width_px, height=height_px)
        self.figure.dpi = int(height_px * 0.0855)

        # Resize the figure
        width_in = width_px / self.figure.dpi
        height_in = height_px / self.figure.dpi
        self.figure.set_size_inches(width_in, height_in, forward=True)
        self.canvas.draw()

    def update_config(self):
        try:
            for field, var in self.inputs.items():
                val = var.get()
                if isinstance(getattr(self.config_data, field), bool):
                    setattr(self.config_data, field, bool(var.get()))
                else:
                    setattr(self.config_data, field, float(val.replace(",", ".")))
        except Exception as e:
            print("Error updating config settings:", e)

    def update_plot(self):
        self.update_config()
        try:
            self.figure.clf()
            self.figure = self.generate_report_figure()
            self.canvas.figure = self.figure
            self.lock_a4_ratio(FakeEvent(self.main_area.winfo_width(), self.main_area.winfo_height()))
            self.canvas.draw()
        except Exception as e:
            print("Error updating plot:", e)

    def save_pdf(self):
        file_path = tkinter.filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.get_report().savepdf(file_path)
            print(f"Saved to {file_path}")


if __name__ == "__main__":
    app = ReportApp()
    app.mainloop()
