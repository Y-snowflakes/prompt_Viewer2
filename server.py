import os
from flask import Flask, render_template, request
from PIL import Image
import piexif
import piexif.helper

app = Flask(__name__)

def read_prompt(file):
    """
    Stable Diffusion系のPNGからプロンプト/パラメータを読み取る
    優先順位:
    1. Pillowのim.info["parameters"] ← A1111の9割以上がここ
    2. ExifのUserComment ← 一部のツール/再保存画像
    3. 生のim.info全体（デバッグ用）
    """
    try:
        # Image.openはファイルポインタを消費するので、seek(0)するかbytesで扱う
        # Flaskのrequest.filesはstreamなので、readしてBytesIOにするのが安全
        file.seek(0)  # ← 重要: 複数回読み込む可能性があるので先頭に戻す
        im = Image.open(file)

        # 1. A1111 / WebUI標準の場所（これが最優先）
        if "parameters" in im.info:
            params = im.info["parameters"].strip()
            if params:
                return params

        # 2. Exif UserComment（ComfyUI一部やNovelAIなど）
        exif_data = im.info.get("exif")
        if exif_data:
            try:
                exif_dict = piexif.load(exif_data)
                user_comment_tag = piexif.ExifIFD.UserComment
                user_comment = exif_dict.get("Exif", {}).get(user_comment_tag)
                if user_comment:
                    # piexifのヘルパーでデコード（ASCII/UNICODE対応）
                    try:
                        decoded = piexif.helper.UserComment.load(user_comment)
                        if decoded.strip():
                            return decoded.strip()
                    except:
                        # フォールバック: 生バイトをUTF-8で無理やり
                        try:
                            return user_comment.decode('utf-8', errors='replace').strip()
                        except:
                            return "[Unknown encoding in UserComment]"

            except Exception as exif_err:
                # Exif壊れても無視して次へ
                pass

        # 3. 何も取れなかったらraw info全部出す（デバッグに便利）
        if im.info:
            raw_info = "\n".join(f"{k}: {v}" for k, v in im.info.items())
            return f"No standard prompt found.\nRaw PNG info:\n{raw_info}"

        return "No metadata found in this image."

    except Exception as e:
        return f"Error reading image: {str(e)}"


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