# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

# sys gives PySide6 access to information about how our Python program was started.
import sys  # Import the system module so the app can start correctly.
# this is imaport the image thst is from the GIU
from main import analyze_image  # Import the image analysis function from the main script.

# Import the GUI components we need.
from PySide6.QtWidgets import (  # Import widgets needed to build the window and controls.
    QApplication,  # Create the Qt application object for the GUI.
    QMainWindow,  # Build the main window container.
    QPushButton,  # Create the button used to choose an image.
    QLabel,  # Create labels for text and preview content.
    QVBoxLayout,  # Arrange widgets vertically in the window.
    QWidget,  # Create the central widget that holds the layout.
    QFileDialog,  # Open a file picker dialog for selecting an image.
    QTextEdit,  # Create the area where analysis results are displayed.
)

# QPixmap allows us to load an image and display it inside our GUI.
from PySide6.QtGui import QPixmap  # Import the image class used to preview selected files.

# Qt gives us useful settings such as alignment and image scaling.
from PySide6.QtCore import Qt  # Import Qt enums for alignment and scaling options.


def normalize_file_selection(selection):
    """Return a plain file path from Qt's tuple-based file selection API."""
    if selection in (None, ""):
        return ""
    if isinstance(selection, (list, tuple)):
        return selection[0] if selection else ""
    return str(selection)


# --------------------------------------------------
# 1. CREATE THE APPLICATION
# --------------------------------------------------

def main():
    """Build and run the GUI application."""
    # Every PySide6 application needs ONE QApplication.
    #
    # Think of QApplication as the thing controlling the entire GUI program.
    app = QApplication(sys.argv)  # Create the application and pass in command-line arguments.

    # --------------------------------------------------
    # 2. CREATE THE MAIN WINDOW
    # --------------------------------------------------

    # QMainWindow creates the actual window that appears on the user's computer.
    window = QMainWindow()  # Create the main application window object.

    # Text displayed at the top of the window.
    window.setWindowTitle("Image Reader AI")  # Set the title shown in the window bar.

    # Starting size of our application.
    #
    # 1000 = width
    # 700 = height
    window.resize(1000, 700)  # Set the initial window size to 1000x700 pixels.

    # --------------------------------------------------
    # 3. CREATE THE CENTRAL WIDGET
    # --------------------------------------------------

    # QMainWindow needs a central widget.
    #
    # This will become the main area where we place everything else.
    central_widget = QWidget()  # Create the main panel that will hold all UI elements.

    # Tell our main window that this is its central widget.
    window.setCentralWidget(central_widget)  # Attach the central widget to the main window.

    # --------------------------------------------------
    # 4. CREATE THE MAIN VERTICAL LAYOUT
    # --------------------------------------------------

    # QVBoxLayout stacks things vertically.
    #
    # Example:
    #
    # Title
    #   ↓
    # Instructions
    #   ↓
    # Button
    #   ↓
    # Main Content
    #
    layout = QVBoxLayout()  # Create a vertical layout that stacks widgets from top to bottom.

    # Put our vertical layout inside the central widget.
    central_widget.setLayout(layout)  # Attach the vertical layout to the central widget.

    # --------------------------------------------------
    # 5. CREATE THE TOP PART OF THE GUI
    # --------------------------------------------------

    # Create the title.
    title = QLabel("Image Reader AI")  # Create the heading label at the top of the window.

    # Create instructions for the user.
    instructions = QLabel("Hey there, welcome to the Image Reader AI! A AI that will read your images and provide a detailed caption of what the AI is seeing. Please select an image to get started.")  # Display the instruction message.
    upload_button = QPushButton("Choose Image")  # Create the button the user clicks to choose a file.

    # Create the image preview area.
    image_preview = QLabel("No image selected")  # Create a placeholder label before an image is chosen.
    image_preview.setAlignment(Qt.AlignCenter)  # Center the text or image within the preview area.
    image_preview.setMinimumHeight(400)  # Give the preview area enough space to display the image.

    # Create the results area.
    chat_display = QTextEdit()  # Create a read-only text box for showing analysis results.
    chat_display.setReadOnly(True)  # Prevent the user from editing the result output.
    chat_display.setPlaceholderText("Image analysis will appear here.")  # Show placeholder text before analysis is complete.

    # Add widgets to the layout.
    layout.addWidget(title)  # Add the title label to the top of the layout.
    layout.addWidget(instructions)  # Add the instruction label below the title.
    layout.addWidget(upload_button)  # Add the upload button.
    layout.addWidget(image_preview)  # Add the image preview area.
    layout.addWidget(chat_display)  # Add the text display area at the bottom.

    # --------------------------------------------------
    # Add color to the background of the GUI, so it looks more visually appealing.
    window.setStyleSheet("background-color: orange;")  # Set the background color of the main window to orange.
    window.setStyleSheet("QLabel { color: white; font-size: 16px; }")  # Set the text color and font size for all QLabel widgets.
    window.setStyleSheet("QPushButton { background-color: white; color: black; font-size: 16px; padding: 10px; }")  # Style the button with a white background and black text.

    # Create the button the user will click when they want to select an image.
    def getting_file():  # Define a function that runs when the upload button is clicked.
        selected_file = QFileDialog.getOpenFileName(  # Open a file dialog and ask the user to pick an image.
            window,  # Connect the dialog to the main window.
            "Choose an Image",  # Title shown in the file picker.
            "",  # Start in the default directory.
            "Images (*.png *.jpg *.jpeg *.webp)"  # Only allow common image file types.
        )
        file_path = normalize_file_selection(selected_file)

        if not file_path:  # Check whether the user canceled the file dialog.
            return  # Exit the function without doing anything else.

        pixmap = QPixmap(file_path)  # Load the selected file as a Qt pixmap for previewing.

        scaled_pixmap = pixmap.scaled(  # Resize the pixmap to fit the preview area.
            600,  # Set a width of 600 pixels.
            400,  # Set a height of 400 pixels.
            Qt.KeepAspectRatio,  # Preserve the image's original proportions.
            Qt.SmoothTransformation  # Use smoothing so the scaled image looks cleaner.
        )

        image_preview.setPixmap(scaled_pixmap)  # Display the resized image in the preview label.

        chat_display.setText("Analyzing image...")  # Show a loading message while the AI works.

        result = analyze_image(file_path)  # Send the selected image file to the analysis function.

        chat_display.setText(str(result))  # Convert the result to text and show it in the output area.

    upload_button.clicked.connect(getting_file)  # Connect the button click to the file selection function.

    window.show()  # Display the main window to the user.
    sys.exit(app.exec())  # Start the Qt event loop and exit cleanly when the app closes.


if __name__ == "__main__":
    main()