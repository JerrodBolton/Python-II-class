# The "Add a Model from Hugging Face" window:
#   [ bartowski/Llama-3.2-3B-Instruct-GGUF               ] [ Find Files ]
#   Llama-3.2-3B-Instruct-Q4_K_M.gguf          2.0 GB      [ Download ]
#   Llama-3.2-3B-Instruct-Q5_K_M.gguf          2.3 GB      [ Download ]
#   [=========-----------]  1.1 GB of 2.3 GB               [ Cancel ]
import threading
import customtkinter as ctk
from theme import colors, radius, font

import hub
import llm

# A good place to start, shown in the box when the window opens
example_repo = "bartowski/Llama-3.2-3B-Instruct-GGUF"


class AddModelDialog(ctk.CTkToplevel):
    # on_use(file_name) is a function from main.py that switches the app to a model
    def __init__(self, master, on_use):
        super().__init__(master, fg_color=colors["background"])
        self.on_use = on_use
        self.download = None
        self.title("Add a Model from Hugging Face")
        self.geometry("680x560")
        # transient() keeps this window on top of the main window
        self.transient(master)
        # If the window is closed in the middle of a download, stop the download too
        self.protocol("WM_DELETE_WINDOW", self.close)

        ctk.CTkLabel(self, text="Add a Model from Hugging Face", font=font(20, "bold"),
                     text_color=colors["text"], anchor="w").pack(fill="x", padx=24, pady=(22, 4))
        ctk.CTkLabel(self, text="Paste a model page name or link. Pages with GGUF in the name have files this app can run.\n"
                                "Q4_K_M or Q5_K_M versions are a good balance of size and quality.",
                     font=font(13), text_color=colors["text_muted"], anchor="w", justify="left").pack(fill="x", padx=24)

        # ---------- The search row ----------
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=24, pady=(16, 8))
        self.repo_entry = ctk.CTkEntry(search_row, font=font(14), height=38, fg_color=colors["input_background"],
                                       border_color=colors["border"], text_color=colors["text"])
        self.repo_entry.insert(0, example_repo)
        self.repo_entry.pack(side="left", fill="x", expand=True)
        # Pressing Enter in the box is the same as clicking Find Files
        self.repo_entry.bind("<Return>", lambda event: self.find_files())
        self.find_button = ctk.CTkButton(search_row, text="Find Files", font=font(14, "bold"), height=38, width=120,
                                         corner_radius=radius["button"], fg_color=colors["primary"],
                                         hover_color=colors["primary_hover"], command=self.find_files)
        self.find_button.pack(side="left", padx=(10, 0))

        self.status_label = ctk.CTkLabel(self, text="", font=font(13), text_color=colors["text_muted"], anchor="w")
        self.status_label.pack(fill="x", padx=24)

        # ---------- The list of files ----------
        self.file_list = ctk.CTkScrollableFrame(self, fg_color=colors["panel"], corner_radius=radius["card"],
                                                border_width=1, border_color=colors["panel_border"])
        self.file_list.pack(fill="both", expand=True, padx=24, pady=(6, 12))

        # ---------- Download progress (hidden until a download starts) ----------
        self.progress_row = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_bar = ctk.CTkProgressBar(self.progress_row, progress_color=colors["secondary"])
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.progress_label = ctk.CTkLabel(self.progress_row, text="", font=font(13), text_color=colors["text"], width=170)
        self.progress_label.pack(side="left", padx=10)
        self.action_button = ctk.CTkButton(self.progress_row, text="Cancel", font=font(14, "bold"), width=150,
                                           corner_radius=radius["button"], fg_color=colors["surface"],
                                           hover_color=colors["surface_hover"], command=self.cancel_download)
        self.action_button.pack(side="left")

        # Bring this window to the front once it has been drawn (needed on macOS)
        self.after(150, self.focus_and_lift)

    def focus_and_lift(self):
        self.lift()
        self.repo_entry.focus_set()

    # ---------- Finding the files on a model page ----------
    def find_files(self):
        repo = hub.parse_repo(self.repo_entry.get())
        if repo is None:
            self.set_status("Type a model name like owner/model-name.", colors["error"])
            return
        self.set_status(f"Looking up {repo}…", colors["text_muted"])
        self.find_button.configure(state="disabled")
        for row in self.file_list.winfo_children():
            row.destroy()

        # Asking the website can take a second, so we do it in a background thread
        # and check back with after() so the window never freezes
        result = {}

        def ask_hugging_face():
            try:
                result["files"] = hub.list_gguf_files(repo)
            except RuntimeError as error:
                result["error"] = str(error)

        thread = threading.Thread(target=ask_hugging_face, daemon=True)
        thread.start()
        self.wait_for_files(thread, result, repo)

    def wait_for_files(self, thread, result, repo):
        if thread.is_alive():
            self.after(100, self.wait_for_files, thread, result, repo)
            return
        self.find_button.configure(state="normal")
        if "error" in result:
            self.set_status(result["error"], colors["error"])
            return
        self.set_status(f"{len(result['files'])} files found on {repo}", colors["secondary"])
        for file in result["files"]:
            self.add_file_row(repo, file)

    # One row in the list: file name, size, and a Download button
    def add_file_row(self, repo, file):
        row = ctk.CTkFrame(self.file_list, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=file["path"], font=font(13), text_color=colors["text"], anchor="w").pack(side="left", padx=(8, 0))
        if file["path"].split("/")[-1] in llm.list_models():
            ctk.CTkLabel(row, text="Downloaded", font=font(13, "bold"), text_color=colors["secondary"],
                         width=110).pack(side="right", padx=8)
        else:
            ctk.CTkButton(row, text="Download", font=font(13, "bold"), width=110, height=30,
                          corner_radius=radius["button"], fg_color=colors["surface"], hover_color=colors["surface_hover"],
                          command=lambda: self.start_download(repo, file)).pack(side="right", padx=8)
        ctk.CTkLabel(row, text=hub.format_size(file["size"]), font=font(13), text_color=colors["text_muted"],
                     width=80).pack(side="right")

    # ---------- Downloading ----------
    def start_download(self, repo, file):
        if self.download is not None and not (self.download.finished or self.download.error or self.download.cancelled):
            self.set_status("Please wait for the current download to finish.", colors["accent"])
            return
        self.download = hub.Download(repo, file["path"])
        self.set_status(f"Downloading {self.download.file_name}…", colors["text_muted"])
        self.progress_bar.set(0)
        self.action_button.configure(text="Cancel", fg_color=colors["surface"],
                                     hover_color=colors["surface_hover"], command=self.cancel_download)
        self.progress_row.pack(fill="x", padx=24, pady=(0, 20))
        self.check_download()

    # Every half second, look at how far the download has got and update the progress bar
    def check_download(self):
        download = self.download
        if download.error:
            self.set_status(download.error, colors["error"])
            self.progress_row.pack_forget()
        elif download.cancelled:
            self.set_status("Download cancelled.", colors["text_muted"])
            self.progress_row.pack_forget()
        elif download.finished:
            self.progress_bar.set(1)
            self.progress_label.configure(text="Done")
            self.set_status(f"{download.file_name} is ready.", colors["secondary"])
            self.action_button.configure(text="Use This Model", fg_color=colors["primary"],
                                         hover_color=colors["primary_hover"], command=self.use_model)
        else:
            if download.total_bytes:
                self.progress_bar.set(download.done_bytes / download.total_bytes)
                self.progress_label.configure(text=f"{hub.format_size(download.done_bytes)} of {hub.format_size(download.total_bytes)}")
            self.after(500, self.check_download)

    def cancel_download(self):
        if self.download is not None:
            self.download.cancel()

    def use_model(self):
        file_name = self.download.file_name
        self.destroy()
        self.on_use(file_name)

    def close(self):
        self.cancel_download()
        self.destroy()

    def set_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)
