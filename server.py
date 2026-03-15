import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)


def read_prompt(file):

    try:

        im = Image.open(file)

        if "parameters" in im.info:
            return im.info["parameters"]

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

    results = []

    if request.method == "POST":

        files = request.files.getlist("files")

        for f in files:

            if f.filename:

                text = read_prompt(f)

                results.append({
                    "name": f.filename,
                    "text": text
                })

    return render_template("index.html", results=results)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)