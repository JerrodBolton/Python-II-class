# The model information header at the top of the chat:
# [ model name card ] [ status ] [ parameters ] [ quantization ] [ context size ] [ max output ]
# Every box is a rounded frame. They sit side by side because we pack them with side="left".

# We use plain tkinter for one thing: the dropdown menu of models, which looks like a normal Mac menu
import tkinter as tk
# customtkinter gives us modern widgets (frames, labels, buttons) built on top of tkinter
import customtkinter as ctk
# Our theme colors, corner sizes and font helper
from theme import colors, radius, font
# load_icon("models", 26, "#18C994") gives us a colored icon
from icons import load_icon


# Helper: a small rounded card with a thin border, used for every box in the header
# A helper function saves us from typing the same 2 lines of settings over and over
def header_card(master):
    return ctk.CTkFrame(master, fg_color=colors["card"], corner_radius=radius["card"],
                        border_width=1, border_color=colors["card_border"])


# One stat box, a big value on top and a small caption under it (like "8,192" / "Context Size")
class StatCard(ctk.CTkFrame):
    #   caption = the small gray words under the value, like "Parameters"
    def __init__(self, master, caption):
        super().__init__(master, fg_color=colors["card"], corner_radius=radius["card"],
                         border_width=1, border_color=colors["card_border"])
        # The value starts as a dash "—" until the model is loaded and we know the real number
        # We save it as self.value_label so set_value() can change it later
        self.value_label = ctk.CTkLabel(self, text="—", font=font(14, "bold"), text_color=colors["text"], anchor="w", height=20)
        self.value_label.pack(fill="x", padx=16, pady=(12, 0))
        # The caption never changes, so we do not need to save it in a variable
        ctk.CTkLabel(self, text=caption, font=font(11), text_color=colors["text_muted"], anchor="w",
                     height=16).pack(fill="x", padx=16, pady=(0, 12))

    # Change the big value, for example set_value("8B")
    def set_value(self, value):
        self.value_label.configure(text=value)


class ModelHeader(ctk.CTkFrame):
    # These are functions from main.py:
    #   list_models() returns the model files we can pick from
    #   on_select_model(file_name) switches to that model
    #   on_add_model() opens the "Add a Model from Hugging Face" window
    def __init__(self, master, list_models, on_select_model, on_add_model):
        # The header itself is see-through, only the cards inside it have a color
        super().__init__(master, fg_color="transparent")
        self.list_models = list_models
        self.on_select_model = on_select_model
        self.on_add_model = on_add_model
        # The file name of the loaded model, so the dropdown can put a check mark next to it
        self.current_file = None

        # ---------- Model name card ----------
        model_card = header_card(self)
        # fill="y" makes this card as tall as the header
        model_card.pack(side="left", fill="y")
        # The small rounded square with the green cube icon
        icon_tile = ctk.CTkFrame(model_card, width=50, height=50, corner_radius=12, fg_color=colors["panel"],
                                 border_width=1, border_color=colors["card_border"])
        icon_tile.pack(side="left", padx=(14, 12), pady=12)
        # place() with relx/rely 0.5 puts the icon exactly in the middle of the tile
        ctk.CTkLabel(icon_tile, text="", image=load_icon("models", 26, colors["secondary"])).place(relx=0.5, rely=0.5, anchor="center")
        # A see-through frame to stack the word "MODEL" on top of the model name
        name_box = ctk.CTkFrame(model_card, fg_color="transparent")
        name_box.pack(side="left", pady=10)
        ctk.CTkLabel(name_box, text="MODEL", font=font(11), text_color=colors["text_muted"], anchor="w", height=14).pack(fill="x")
        # Shows "Loading…" until the model is ready, then set_model_info() puts the real name here
        self.model_name_label = ctk.CTkLabel(name_box, text="Loading…", font=font(17), text_color=colors["text"], anchor="w", height=24)
        self.model_name_label.pack(fill="x")
        # The dropdown arrow
        chevron = ctk.CTkLabel(model_card, text="", image=load_icon("chevron_down", 20, colors["text_muted"]))
        chevron.pack(side="left", padx=(16, 18))
        # Clicking anywhere on the model card opens the dropdown, so we bind the click to every piece of it
        self.model_card = model_card
        for widget in [model_card, icon_tile, name_box, chevron, *icon_tile.winfo_children(), *name_box.winfo_children()]:
            widget.bind("<Button-1>", self.open_model_menu)
            widget.configure(cursor="pointinghand")

        # ---------- Connection status ----------
        status_card = header_card(self)
        # expand=True lets the status and stat cards share the leftover width, like the design
        status_card.pack(side="left", fill="both", expand=True, padx=(12, 0))
        # Top row: the colored dot and the status words, side by side
        status_row = ctk.CTkFrame(status_card, fg_color="transparent")
        status_row.pack(fill="x", padx=18, pady=(14, 0))
        # "●" is a text character, so we can change its color with text_color
        self.status_dot = ctk.CTkLabel(status_row, text="●", font=font(13), height=18)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = ctk.CTkLabel(status_row, text="", font=font(14, "bold"), height=18)
        self.status_label.pack(side="left")
        # padx=(37, 18): the big left padding lines "Local Inference" up under the status words, not the dot
        ctk.CTkLabel(status_card, text="Local Inference", font=font(11), text_color=colors["text_muted"],
                     anchor="w", height=16).pack(fill="x", padx=(37, 18), pady=(0, 12))
        # Start in the orange "Loading model…" state
        self.set_status("loading")

        # ---------- Stat cards ----------
        # A dictionary so we can find each card by its key: self.stat_cards["parameters"]
        # The keys match the keys in llm.model_info(), which makes set_model_info() simple
        self.stat_cards = {}
        for key, caption in [("parameters", "Parameters"), ("quantization", "Quantization"),
                             ("context_size", "Context Size"), ("max_output", "Max Output")]:
            card = StatCard(self, caption)
            card.pack(side="left", fill="both", expand=True, padx=(10, 0))
            self.stat_cards[key] = card

    # ---------- The model dropdown ----------
    # Runs when you click the model card. Builds a menu of every model, plus "Add a model…"
    def open_model_menu(self, event=None):
        menu = tk.Menu(self, tearoff=False)
        for file_name in self.list_models():
            # A check mark next to the model that is loaded right now
            mark = "✓  " if file_name == self.current_file else "     "
            # lambda f=file_name remembers THIS file name for each menu item
            menu.add_command(label=mark + file_name, command=lambda f=file_name: self.on_select_model(f))
        menu.add_separator()
        menu.add_command(label="Add a model from Hugging Face…", command=self.on_add_model)
        # Show the menu just under the model card
        x = self.model_card.winfo_rootx()
        y = self.model_card.winfo_rooty() + self.model_card.winfo_height() + 4
        menu.tk_popup(x, y)

    # Fill in the header with real facts from llm.model_info()
    # info is a dictionary like {"name": "Dolphin 3.0 Llama 3.1 8B", "parameters": "8B", ...}
    def set_model_info(self, info):
        self.current_file = info["file"]
        self.model_name_label.configure(text=info["name"])
        self.stat_cards["parameters"].set_value(info["parameters"])
        self.stat_cards["quantization"].set_value(info["quantization"])
        # {:,} adds commas: 8192 -> "8,192"
        self.stat_cards["context_size"].set_value(f"{info['context_size']:,}")
        self.stat_cards["max_output"].set_value(f"{info['max_output']:,}")

    # state is "loading", "connected" or "error"
    # Green "Connected" when the model is ready, red if it failed, orange "Loading model…" before that
    def set_status(self, state):
        if state == "connected":
            color, text = colors["secondary"], "Connected"
        elif state == "error":
            color, text = colors["error"], "Could not load model"
        else:
            color, text = colors["primary"], "Loading model…"
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)
