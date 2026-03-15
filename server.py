import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)

def read_prompt(path):
    try:
        with Image.open(path) as im:  # withで安全にclose
            # 1. PNG/A1111標準のparameters（これが最優先）
            if "parameters" in im.info and im.info["parameters"].strip():
                return im.info["parameters"].strip()

            # 2. Exif UserComment（一部のWEBP/JPGでここ）
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

            # 3. WEBP特有の追加チェック（XMPや他のinfoキー）← これが効くことが多い
            # Stable Diffusion WEBPでたまに "xmp" や "XML:com.adobe.xmp" に入る
            for key in im.info:
                val = im.info[key]
                if isinstance(val, str) and ("parameters" in val.lower() or "Negative prompt:" in val):
                    return val.strip()
                if isinstance(val, bytes):
                    try:
                        decoded_val = val.decode('utf-8', errors='ignore').strip()
                        if "parameters" in decoded_val or "Negative prompt:" in decoded_val:
                            return decoded_val
                    except:
                        pass

            # 4. デバッグ用：raw info全部出力（どのキーに入ってるか分かる）
            if im.info:
                raw_output = []
                for k, v in im.info.items():
                    if isinstance(v, bytes):
                        try:
                            preview = v.decode('utf-8', errors='ignore')[:200]
                        except:
                            preview = "[binary data]"
                    else:
                        preview = str(v)[:200]
                    raw_output.append(f"{k}: {preview}")
                return "No standard parameters found in WEBP/PNG.\nRaw im.info:\n" + "\n".join(raw_output)

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