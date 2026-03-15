import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)

def read_prompt(path):
    try:
        with Image.open(path) as im:  # withで自動close、安全
            # WEBP/PNG/JPG共通でこれが一番多い（A1111標準）
            if "parameters" in im.info:
                params = im.info["parameters"].strip()
                if params:
                    return params

            # Exif UserCommentのフォールバック（一部の再保存WEBPなど）
            exif = im.info.get("exif")
            if exif:
                try:
                    exif_dict = piexif.load(exif)
                    comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
                    if comment:
                        # piexifヘルパーでデコード（UTF-8/ASCII対応）
                        decoded = piexif.helper.UserComment.load(comment)
                        if decoded.strip():
                            return decoded.strip()
                except Exception:
                    pass  # Exif壊れても無視

            # 何も取れなかった場合のデバッグ情報
            if im.info:
                raw = "\n".join(f"{k}: {v[:100]}..." for k, v in im.info.items())  # 長すぎ防止
                return f"No parameters found.\nRaw info (partial):\n{raw}"

            return "No metadata found"

    except Exception as e:
        return f"Error reading {os.path.basename(path)}: {str(e)}"
    
    
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