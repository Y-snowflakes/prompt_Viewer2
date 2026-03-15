import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)

def read_prompt(path):
    try:
        with Image.open(path) as im:  # ← with文で自動close（推奨）
            # A1111標準のparameters（PNG/WEBP共通でこれが9割）
            if "parameters" in im.info:
                params = im.info["parameters"].strip()
                if params:  # 空文字列回避
                    return params

            # Exif UserComment（フォールバック）
            exif = im.info.get("exif")
            if exif:
                try:
                    exif_dict = piexif.load(exif)
                    comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                    if comment:
                        decoded = piexif.helper.UserComment.load(comment)
                        if decoded.strip():
                            return decoded.strip()
                except Exception:
                    pass  # Exif壊れても無視

            # デバッグ用：raw infoを少し出す（問題診断に便利）
            if im.info:
                raw_lines = [f"{k}: {v[:100]}..." for k, v in im.info.items() if v]
                return "No 'parameters' found.\nPartial raw info:\n" + "\n".join(raw_lines)

            return "No metadata"

    except Exception as e:
        return f"Read error: {str(e)}"
    

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