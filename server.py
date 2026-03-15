import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)

def read_prompt(path):
    try:
        with Image.open(path) as im:
            # 1. 標準parameters（PNGで効く、WEBPでも稀に入る）
            if "parameters" in im.info and im.info["parameters"].strip():
                return im.info["parameters"].strip()

            # 2. Exif UserComment（標準フォールバック）
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
                    pass

            # 3. WEBP/JPGでメタデータが他のキーに入っている場合を総スキャン
            #    "parameters", "Negative prompt:", "Steps:" などのキーワードで探す
            candidate = ""
            for key, value in im.info.items():
                if isinstance(value, str):
                    val_str = value.strip()
                    if any(kw in val_str for kw in ["parameters", "Negative prompt:", "Steps:", "Seed:", "CFG scale:"]):
                        if len(val_str) > len(candidate):  # 長い方を優先
                            candidate = val_str
                elif isinstance(value, bytes):
                    try:
                        val_decoded = value.decode('utf-8', errors='ignore').strip()
                        if any(kw in val_decoded for kw in ["parameters", "Negative prompt:", "Steps:"]):
                            if len(val_decoded) > len(candidate):
                                candidate = val_decoded
                    except:
                        pass

            if candidate:
                return candidate

            # 4. 最終手段：raw info全部出力（これを見ればどこに入ってるか分かる！）
            if im.info:
                raw_lines = []
                for k, v in im.info.items():
                    preview = str(v)[:300] if isinstance(v, str) else "[binary or non-str data]"
                    raw_lines.append(f"{k}: {preview}")
                return "WEBP/PNG metadata found but no standard prompt.\nRaw im.info dump:\n" + "\n".join(raw_lines)

            return "No metadata at all"

    except Exception as e:
        return f"Error opening {os.path.basename(path)}: {str(e)}"
    

    
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