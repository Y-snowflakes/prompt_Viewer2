import os
from flask import Flask, render_template, request, jsonify
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)


def read_prompt(file):

    try:

        im = Image.open(file)

        # PNG parameters
        if "parameters" in im.info and im.info["parameters"].strip():
            return im.info["parameters"]

        # EXIF (WEBP/JPG)
        exif = im.info.get("exif")

        if exif:

            try:

                exif_dict = piexif.load(exif)

                comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)

                if comment:

                    decoded = piexif.helper.UserComment.load(comment)

                    if decoded.strip():
                        return decoded

            except:
                pass

        # その他メタデータ総スキャン
        for k, v in im.info.items():

            if isinstance(v, bytes):

                try:
                    text = v.decode("utf-8", "ignore")

                    if "Steps:" in text:
                        return text

                except:
                    pass

            if isinstance(v, str):

                if "Steps:" in v:
                    return v

        return "No metadata"

    except Exception as e:

        return str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/read", methods=["POST"])
def read():

    file = request.files["file"]

    text = read_prompt(file)

    return jsonify({"text": text})


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
    