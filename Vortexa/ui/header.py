# The model information header at the top of the chat:
# [ model name card ] [ status ] [ parameters ] [ quantization ] [ context size ] [ max output ]
import customtkinter as ctk
from theme import colors, radius, font
from icons import load_icon


# Helper: a small rounded card with a thin border, used for every box in the header
def header_card(master):
    return ctk.CTkFrame(master, fg_color=colors["card"], corner_radius=radius["card"],
                        border_width=1, border_color=colors["card_border"])


# One stat box, a big value on top and a small caption under it (like "8,192" / "Context Size")
class StatCard(ctk.CTkFrame):
    def __init__(self, master, caption):
        super().__init__(master, fg_color=colors["card"], corner_radius=radius["card"],
                         border_width=1, border_color=colors["card_border"])
        self.value_label = ctk.CTkLabel(self, text="—", font=font(14, "bold"), text_color=colors["text"], anchor="w", height=20)
        self.value_label.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(self, text=caption, font=font(11), text_color=colors["text_muted"], anchor="w",
                     height=16).pack(fill="x", padx=16, pady=(0, 12))

    def set_value(self, value):
        self.value_label.configure(text=value)


class ModelHeader(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # ---------- Model name card ----------
        model_card = header_card(self)
        model_card.pack(side="left", fill="y")
        icon_tile = ctk.CTkFrame(model_card, width=50, height=50, corner_radius=12, fg_color=colors["panel"],
                                 border_width=1, border_color=colors["card_border"])
        icon_tile.pack(side="left", padx=(14, 12), pady=12)
        ctk.CTkLabel(icon_tile, text="", image=load_icon("models", 26, colors["secondary"])).place(relx=0.5, rely=0.5, anchor="center")
        name_box = ctk.CTkFrame(model_card, fg_color="transparent")
        name_box.pack(side="left", pady=10)
        ctk.CTkLabel(name_box, text="MODEL", font=font(11), text_color=colors["text_muted"], anchor="w", height=14).pack(fill="x")
        self.model_name_label = ctk.CTkLabel(name_box, text="Loading…", font=font(17), text_color=colors["text"], anchor="w", height=24)
        self.model_name_label.pack(fill="x")
        # The dropdown arrow. Switching models comes in a later milestone, for now it is just the icon.
        ctk.CTkLabel(model_card, text="", image=load_icon("chevron_down", 20, colors["text_muted"])).pack(side="left", padx=(16, 18))

        # ---------- Connection status ----------
        status_card = header_card(self)
        # expand=True lets the status and stat cards share the leftover width, like the design
        status_card.pack(side="left", fill="both", expand=True, padx=(12, 0))
        status_row = ctk.CTkFrame(status_card, fg_color="transparent")
        status_row.pack(fill="x", padx=18, pady=(14, 0))
        self.status_dot = ctk.CTkLabel(status_row, text="●", font=font(13), height=18)
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_label = ctk.CTkLabel(status_row, text="", font=font(14, "bold"), height=18)
        self.status_label.pack(side="left")
        ctk.CTkLabel(status_card, text="Local Inference", font=font(11), text_color=colors["text_muted"],
                     anchor="w", height=16).pack(fill="x", padx=(37, 18), pady=(0, 12))
        self.set_status("loading")

        # ---------- Stat cards ----------
        self.stat_cards = {}
        for key, caption in [("parameters", "Parameters"), ("quantization", "Quantization"),
                             ("context_size", "Context Size"), ("max_output", "Max Output")]:
            card = StatCard(self, caption)
            card.pack(side="left", fill="both", expand=True, padx=(10, 0))
            self.stat_cards[key] = card

    # Fill in the header with real facts from llm.model_info()
    def set_model_info(self, info):
        self.model_name_label.configure(text=info["name"])
        self.stat_cards["parameters"].set_value(info["parameters"])
        self.stat_cards["quantization"].set_value(info["quantization"])
        # {:,} adds commas: 8192 -> "8,192"
        self.stat_cards["context_size"].set_value(f"{info['context_size']:,}")
        self.stat_cards["max_output"].set_value(f"{info['max_output']:,}")

    # state is "loading" or "connected"
    def set_status(self, state):
        if state == "connected":
            color, text = colors["secondary"], "Connected"
        else:
            color, text = colors["primary"], "Loading model…"
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)
