from gui_test import normalize_file_selection


def test_normalize_file_selection_tuple():
    assert normalize_file_selection(("/tmp/photo.png", "Images (*.png)")) == "/tmp/photo.png"


def test_normalize_file_selection_empty():
    assert normalize_file_selection(("", "")) == ""


def test_normalize_file_selection_string():
    assert normalize_file_selection("/tmp/photo.png") == "/tmp/photo.png"
