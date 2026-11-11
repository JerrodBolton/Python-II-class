# This file talks to Hugging Face (huggingface.co), the website where people share AI models.
# It does two things:
#   1. list_gguf_files() asks Hugging Face which .gguf model files a model page has
#   2. Download copies one of those files into our models folder
# The GUI (ui/add_model_dialog.py) calls these, it never talks to the internet itself.
import os
import re
import ssl
import json
import threading
import urllib.request
import urllib.error
# certifi gives Python the list of trusted website certificates.
# Without it, Python from python.org on a Mac cannot open https:// links.
import certifi

from llm import models_folder

# One secure connection setting that we reuse for every request
_ssl_context = ssl.create_default_context(cafile=certifi.where())

# Some models (like Meta's official Llama pages) need you to log in and accept a license.
# If you make a token at huggingface.co/settings/tokens and run the app with
#   HF_TOKEN=hf_yourtoken .venv/bin/python main.py
# we send it along so those downloads work too.
_token = os.environ.get("HF_TOKEN")


# Open a Hugging Face link, with our certificates and token added
def _open(url):
    request = urllib.request.Request(url, headers={"User-Agent": "VORTEXA"})
    if _token:
        request.add_header("Authorization", "Bearer " + _token)
    return urllib.request.urlopen(request, context=_ssl_context, timeout=30)


# People paste model names in different ways. All of these mean the same model:
#   bartowski/Llama-3.2-3B-Instruct-GGUF
#   https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
#   https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/tree/main
# This turns any of them into just "bartowski/Llama-3.2-3B-Instruct-GGUF", or None if it is not a model name.
def parse_repo(text):
    text = text.strip().removeprefix("https://").removeprefix("http://").removeprefix("huggingface.co/")
    parts = text.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return parts[0] + "/" + parts[1]


# Big models are split into pieces like "model-00001-of-00003.gguf". We skip those to keep things simple.
_split_file = re.compile(r"-\d{5}-of-\d{5}\.gguf$")


# Ask Hugging Face for every .gguf file on a model page.
# Returns a list like [{"path": "Llama-3.2-3B-Instruct-Q5_K_M.gguf", "size": 2322154016}, ...]
# If something goes wrong it raises an error with a friendly message to show in the app.
def list_gguf_files(repo):
    url = f"https://huggingface.co/api/models/{repo}/tree/main?recursive=true"
    try:
        with _open(url) as response:
            items = json.load(response)
    except urllib.error.HTTPError as error:
        # Hugging Face answers "401" both for models that do not exist and for ones that need a login
        if error.code in (401, 403):
            raise RuntimeError(f"Could not find {repo}. Check the spelling, or it may need a Hugging Face login (see HF_TOKEN in hub.py).")
        if error.code == 404:
            raise RuntimeError(f"Could not find a model called {repo} on Hugging Face.")
        raise RuntimeError(f"Hugging Face said: error {error.code}.")
    except urllib.error.URLError:
        raise RuntimeError("Could not reach Hugging Face. Check your internet connection.")

    files = []
    for item in items:
        path = item.get("path", "")
        if item.get("type") == "file" and path.lower().endswith(".gguf") and not _split_file.search(path):
            # Big files are stored with "LFS", which keeps their real size in item["lfs"]["size"]
            size = item.get("lfs", {}).get("size", item.get("size", 0))
            files.append({"path": path, "size": size})
    if not files:
        raise RuntimeError("That model has no .gguf files. Look for a page with GGUF in its name.")
    # Smallest first, so the quick-to-download versions are at the top
    return sorted(files, key=lambda f: f["size"])


# Turn a number of bytes into something readable: 2322154016 -> "2.3 GB"
def format_size(num_bytes):
    if num_bytes >= 1_000_000_000:
        return f"{num_bytes / 1_000_000_000:.1f} GB"
    return f"{num_bytes / 1_000_000:.0f} MB"


# Downloading a 5 GB file takes minutes. If we did it the normal way the whole window would freeze.
# So a Download runs in a background "thread" (a second worker running at the same time),
# and the GUI checks on it every so often by reading .done_bytes, .finished and .error.
class Download:
    def __init__(self, repo, path):
        self.repo = repo
        # Files can sit in sub-folders on Hugging Face, but we save them straight into models/
        self.file_name = os.path.basename(path)
        self.url = f"https://huggingface.co/{repo}/resolve/main/{path}"
        self.total_bytes = 0
        self.done_bytes = 0
        self.finished = False
        self.error = None
        self.cancelled = False
        threading.Thread(target=self._run, daemon=True).start()

    def cancel(self):
        self.cancelled = True

    def _run(self):
        os.makedirs(models_folder, exist_ok=True)
        final_path = os.path.join(models_folder, self.file_name)
        # We download into "name.gguf.part" and only rename it when it is complete,
        # so a half-downloaded file never shows up in the model list
        part_path = final_path + ".part"
        try:
            with _open(self.url) as response, open(part_path, "wb") as out_file:
                self.total_bytes = int(response.headers.get("Content-Length", 0))
                while not self.cancelled:
                    block = response.read(1024 * 1024)  # 1 MB at a time
                    if not block:
                        break
                    out_file.write(block)
                    self.done_bytes += len(block)
            if self.cancelled:
                os.remove(part_path)
                return
            os.replace(part_path, final_path)
            self.finished = True
        except Exception as error:
            if os.path.exists(part_path):
                os.remove(part_path)
            if isinstance(error, urllib.error.HTTPError) and error.code in (401, 403):
                self.error = "This model needs a Hugging Face login. See the HF_TOKEN note in hub.py."
            else:
                self.error = f"Download failed: {error}"
