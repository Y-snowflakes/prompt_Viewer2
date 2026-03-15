import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)


def read_prompt(file):

    try:

        im = Image.open(file)

        # Stable Diffusion PNG
        if "parameters" in im.info:
            return im.info["parameters"]

        # EXIF
        exif = im.info.get("exif")

        if exif:

            exif_dict = piexif.load(exif)

            comment = exif_dict["Exif"].get(
                piexif.ExifIFD.UserComment
            )

            if comment:
                return piexif.helper.UserComment.load(comment)

        return str(im.info)

    except Exception as e:

        return f"Error: {e}"


@app.route("/", methods=["GET", "POST"])
def index():

    text = ""

    if request.method == "POST":

        if "file" not in request.files:
            return "No file uploaded"

        file = request.files["file"]

        if file.filename == "":
            return "Empty file"

        text = read_prompt(file)

        return render_template("index.html", text=text)

    return render_template("index.html", text=text)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)