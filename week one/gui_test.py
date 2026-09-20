import sys

# Import the GUI components we need from PySide6.
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
)

# QPixmap loads images so that we can display them in a label.
from PySide6.QtGui import QPixmap
# Qt provides settings for alignment and image scaling.
from PySide6.QtCore import Qt


# --------------------------------------------------
# 1. CREATE THE APPLICATION
# --------------------------------------------------

# QApplication controls the entire GUI application.
# Every PySide6 GUI needs one QApplication.
app = QApplication(sys.argv)


# --------------------------------------------------
# 2. CREATE THE MAIN WINDOW AND GIVE IT A TITLE
# --------------------------------------------------

# QMainWindow is the main window the user will see.
window = QMainWindow()

# Give the window a title.
window.setWindowTitle("Image Reader AI")

# Set the starting width and height in pixels.
window.resize(1000, 700)


# --------------------------------------------------
# 3. CREATE A CENTRAL WIDGET
# --------------------------------------------------

# QMainWindow needs a central widget before we can
# easily place other widgets inside of it.
central_widget = QWidget()

# Tell the main window to use this widget as its main area.
window.setCentralWidget(central_widget)


# --------------------------------------------------
# 4. CREATE A LAYOUT
# --------------------------------------------------

# QVBoxLayout means "Vertical Box Layout."
# Anything we add to this layout will be stacked vertically:
#
# Widget 1
# Widget 2
# Widget 3
layout = QVBoxLayout()

# Put the layout inside our central widget.
central_widget.setLayout(layout)


# --------------------------------------------------
# 5. CREATE OUR FIRST WIDGETS
# --------------------------------------------------

# QLabel displays text on the screen.
title = QLabel("Image Reader AI")

# Another label with instructions for the user.
# This version previews images; AI analysis can be connected later.
instructions = QLabel("Choose an image to preview it.")

# QPushButton creates a clickable button.
upload_button = QPushButton("Choose Image")


# --------------------------------------------------
# 6. ADD THE WIDGETS TO THE LAYOUT
# --------------------------------------------------

# Remember: this is a vertical layout.
# They will appear in the order we add them.
layout.addWidget(title)
layout.addWidget(instructions)
layout.addWidget(upload_button)

# QLabel can display more than just text.
# It can also display an image using QPixmap.
image_preview = QLabel("The image will show here")

# Center whatever is inside the label.
image_preview.setAlignment(Qt.AlignCenter)

# Reserve a preview area at least 600 pixels wide and 400 tall.
image_preview.setMinimumSize(600, 400)
layout.addWidget(image_preview)


# --------------------------------------------------
# 7. CREATE THE BUTTON ACTION
# --------------------------------------------------

def getting_file():
    """Open the image picker when the user clicks Choose Image."""
    # Open the file browser. getOpenFileName() returns two values:
    # the selected file's path and the selected file filter.
    file_path, selected_filter = QFileDialog.getOpenFileName(
        window,                         # Parent window
        "Choose an Image",              # File browser title
        "",                             # Use the default starting folder
        "Images (*.png *.jpg *.jpeg *.webp)",
    )

    # Cancel returns an empty path. Leave the existing preview alone.
    if not file_path:
        return

    # Check the extension before loading. lower() also accepts .JPG, etc.
    # Each extension needs its leading dot, including ".jpg".
    if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        pixmap = QPixmap(file_path)

        # A supported extension does not guarantee a readable image.
        # If loading fails, explain the problem and keep the old preview.
        if pixmap.isNull():
            QMessageBox.warning(window, "Unable to Open Image",
                                "The selected image could not be loaded.")
            return

        # Fit the image within 600 x 400 without stretching its proportions.
        # SmoothTransformation improves the quality of the resized image.
        scaled_pixmap = pixmap.scaled(
            600,
            400,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        # Keep this inside the image branch: scaled_pixmap exists only
        # after a supported image has been loaded and scaled successfully.
        image_preview.setPixmap(scaled_pixmap)
    else:
        QMessageBox.warning(window, "Unsupported Image",
                            "Please choose a PNG, JPG, JPEG, or WEBP image.")


# --------------------------------------------------
# 8. CONNECT THE BUTTON TO THE FUNCTION
# --------------------------------------------------

# "clicked" is a signal. When the button emits it, Qt calls getting_file.
# Connect once, outside the function, so clicks do not add more connections.
upload_button.clicked.connect(getting_file)

# Make the window visible before starting the event loop.
window.show()


# --------------------------------------------------
# 9. START THE EVENT LOOP
# --------------------------------------------------

# Keep the application running and listening for:
# - mouse clicks
# - keyboard input
# - button presses
# - window resizing
# - closing the window
# sys.exit() passes the application's exit code back to Python.
sys.exit(app.exec())
