# https://pypi.org/project/pytesseract/
# py -m pip install pytesseract

from PIL import Image
import pytesseract
import sys

class Tesseract:

    def __init__(self, path=None):
        path = Tesseract.make_path_safe(path)
        self.tess_path = path
        if path is not None:
            pytesseract.pytesseract.tesseract_cmd = path

    def image_to_string(self, filename):
        filename = Tesseract.make_path_safe(filename)
        try:
            image = Image.open(filename)
        except FileNotFoundError as e:
            print("Could not find file for Image object", file=sys.stderr)
            return None

        try:
            return pytesseract.image_to_string(image)
        except FileNotFoundError as e:
            print("Could not find file for text extraction", file=sys.stderr)
            return None
        except pytesseract.pytesseract.TesseractNotFoundError as e:
            print("Ensure Tesseract is on your path", file=sys.stderr)
            return None
        
        return None

    @staticmethod
    def make_path_safe(path):
        return path if path is None else path.replace("\\", "/")


if __name__ == "__main__":
    # Usage: tesseract.py <tesseract path> <image path> [output path]

    if len(sys.argv) < 3:
        sys.exit(1)

    image_filename = sys.argv[2]

    tess_path = None
    if sys.argv[1] != "None":
        tess_path = sys.argv[1]

    tess = Tesseract(tess_path)
    image_text = None
    try:
        image_text = tess.image_to_string(image_filename)
    except:
        sys.exit(2)

    if len(sys.argv) == 4:
        # A filename was provided for the output
        with open(sys.argv[3], "w") as f:
            f.write(image_text)
    else:
        # Explicitly print to stdout
        print(image_text, file=sys.stdout)