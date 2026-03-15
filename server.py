import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)

def read_prompt(file):
    try:
        file.seek(0)  # FlaskのUploadedFileはポインタが進むので必須
        im = Image.open(file)

        # 1. A1111標準（これが最優先・文字化けしにくい）
        if "parameters" in im.info:
            params = im.info["parameters"].strip()
            if params:
                return params

        # 2. Exif UserComment（piexifヘルパーで安全にデコード）
        exif = im.info.get("exif")
        if exif:
            try:
                exif_dict = piexif.load(exif)
                comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
                if comment:
                    # piexifの専用デコーダーを使う → 文字化けしにくい
                    return piexif.helper.UserComment.load(comment).strip()
            except:
                pass  # Exif壊れても無視

        # 3. フォールバック（raw info）
        if im.info:
            return "No standard metadata.\nRaw info:\n" + "\n".join(
                f"{k}: {v}" for k, v in im.info.items()
            )

        return "No metadata found"

    except Exception as e:
        return f"Error: {str(e)}"


@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        files = request.files.getlist("files")

        for f in files:
            if f and f.filename:  # 空ファイル回避
                # 拡張子チェック（画像だけ処理）
                ext = os.path.splitext(f.filename)[1].lower()
                if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
                    results.append({
                        "name": f.filename,
                        "text": "Skipped: Not a supported image format (png/jpg/webp)"
                    })
                    continue

                text = read_prompt(f)
                results.append({
                    "name": f.filename,
                    "text": text
                })

    return render_template("index.html", results=results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)  # debug=Trueで開発中便利（本番ではFalseに）