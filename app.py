import streamlit as st
import math
import io
import os
import urllib.request
import zipfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

st.set_page_config(page_title="モザイクアート自動設計システム", layout="wide")

st.title("🎨 モザイクアート自動設計システム")
st.write("画像をアップロードするだけで、全校生徒で分担して色塗りできるA4サイズの設計図（PDF）を自動生成します。")

# ==========================================
# 1. 基本設定（サイドバー）
# ==========================================
st.sidebar.header("⚙️ 基本設定")
target_area = st.sidebar.number_input("1. 目標とする総枚数（全校生徒数など）", min_value=1, value=100, step=5)

cell_options = {
    "パターン1（縦10マス × 横16マス / A4:約1.7cm角, A5:約1.2cm角）": (16, 10),
    "パターン2（縦13マス × 横21マス / A4:約1.3cm角, A5:約9mm角）": (21, 13),
    "パターン3（縦16マス × 横26マス / A4:約1cm角, A5:約7mm角）": (26, 16),
    "パターン4（縦20マス × 横32マス / A4:約8mm角, A5:約6mm角）": (32, 20),
    "パターン5（縦26マス × 横42マス / A4:約6mm角, A5:約4mm角）": (42, 26),
    "パターン6（縦32マス × 横52マス / A4:約5mm角, A5:約3.5mm角）": (52, 32)
}
cell_choice = st.sidebar.selectbox("2. マス目の細かさ", list(cell_options.keys()), index=2)
CELLS_W, CELLS_H = cell_options[cell_choice]

palette_options = {
    "クーピー12色（標準）": [
        {"name": "あか", "char": "赤", "rgb": (230, 0, 18)}, {"name": "だいだい", "char": "橙", "rgb": (243, 152, 0)},
        {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)}, {"name": "きみどり", "char": "草", "rgb": (143, 195, 31)},
        {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)}, {"name": "みずいろ", "char": "水", "rgb": (0, 160, 233)},
        {"name": "あお", "char": "青", "rgb": (0, 104, 183)}, {"name": "むらさき", "char": "紫", "rgb": (146, 7, 131)},
        {"name": "ももいろ", "char": "桃", "rgb": (228, 0, 127)}, {"name": "ちゃいろ", "char": "茶", "rgb": (143, 84, 44)},
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ],
    "プロッキー12色": [
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "むらさき", "char": "紫", "rgb": (146, 7, 131)},
        {"name": "あお", "char": "青", "rgb": (0, 104, 183)}, {"name": "みずいろ", "char": "水", "rgb": (0, 160, 233)},
        {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)}, {"name": "きみどり", "char": "草", "rgb": (143, 195, 31)},
        {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)}, {"name": "だいだい", "char": "橙", "rgb": (243, 152, 0)},
        {"name": "ソフトピンク", "char": "桃", "rgb": (255, 153, 204)}, {"name": "あか", "char": "赤", "rgb": (230, 0, 18)},
        {"name": "おうどいろ", "char": "黄土", "rgb": (204, 153, 51)}, {"name": "ちゃいろ", "char": "茶", "rgb": (143, 84, 44)},
        {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ],
    "プロッキー10色": [
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "あお", "char": "青", "rgb": (0, 104, 183)},
        {"name": "みずいろ", "char": "水", "rgb": (0, 160, 233)}, {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)},
        {"name": "きみどり", "char": "草", "rgb": (143, 195, 31)}, {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)},
        {"name": "だいだい", "char": "橙", "rgb": (243, 152, 0)}, {"name": "あか", "char": "赤", "rgb": (230, 0, 18)},
        {"name": "ソフトピンク", "char": "桃", "rgb": (255, 153, 204)}, {"name": "むらさき", "char": "紫", "rgb": (146, 7, 131)},
        {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ],
    "プロッキー8色": [
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "あお", "char": "青", "rgb": (0, 104, 183)},
        {"name": "みずいろ", "char": "水", "rgb": (0, 160, 233)}, {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)},
        {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)}, {"name": "ソフトピンク", "char": "桃", "rgb": (255, 153, 204)},
        {"name": "あか", "char": "赤", "rgb": (230, 0, 18)}, {"name": "ちゃいろ", "char": "茶", "rgb": (143, 84, 44)},
        {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ]
}
palette_choice = st.sidebar.selectbox("3. 使用する画材", list(palette_options.keys()))
SELECTED_PALETTE = palette_options[palette_choice]

# ==========================================
# 2. 事前ガイド（推奨サイズ計算）
# ==========================================
st.subheader("💡 ステップ1：代表的な画像比率と最適な用紙枚数")
st.info(f"目標枚数（{target_area} 枚）を上回りつつ、上限約15%の範囲内で最も形が美しくなる設定を計算しました。\n\n※以下の予想サイズは、**周囲の余白をカットし、色塗り部分のみを連結させた「真の完成サイズ」**です。")

ratios = {
    "16:9 (動画・スマホ横)": 16/9,
    " 3:2 (一眼レフ写真)": 3/2,
    " 4:3 (デジカメ・iPad)": 4/3,
    " 1:1 (正方形など)": 1/1
}

# 印刷用紙ごとの「色塗り部分のみ」の物理寸法（単位: メートル）
# A4: 幅は左右15mmずつカット(-30mm)、高さは上下15mmずつ＋ヘッダー15mmカット(-45mm)
PAINTED_W_A4 = 0.267
PAINTED_H_A4 = 0.165
# 縮小・拡大印刷時の色塗り部分の寸法（A4からの倍率で計算）
PAINTED_W_A3, PAINTED_H_A3 = PAINTED_W_A4 * (420/297), PAINTED_H_A4 * (297/210)
PAINTED_W_B5, PAINTED_H_B5 = PAINTED_W_A4 * (257/297), PAINTED_H_A4 * (182/210)
PAINTED_W_A5, PAINTED_H_A5 = PAINTED_W_A4 * (210/297), PAINTED_H_A4 * (148/210)

default_h, default_w = 10, 10
cols = st.columns(2)

for i, (name, ratio) in enumerate(ratios.items()):
    # 画像の比率(ratio)になるように、色塗り部分の寸法ベースで必要な縦横の枚数比を計算
    target_W_to_H = ratio * (PAINTED_H_A4 / PAINTED_W_A4)
    base_h = math.sqrt(target_area / target_W_to_H)
    
    best_w, best_h = 0, 0
    best_score = float('inf')
    max_allowed = target_area * 1.15
    found_within_limit = False
    
    for h in range(max(1, math.floor(base_h) - 10), math.ceil(base_h) + 15):
        ideal_w = h * target_W_to_H
        for w in range(max(1, math.floor(ideal_w) - 2), math.ceil(ideal_w) + 3):
            total = w * h
            if total >= target_area:
                area_penalty = (total - target_area) / target_area
                aspect_penalty = abs((w / h) - target_W_to_H) / target_W_to_H
                
                if total <= max_allowed:
                    score = area_penalty + aspect_penalty * 5.0
                    if score < best_score or not found_within_limit:
                        best_score = score
                        best_w = w
                        best_h = h
                        found_within_limit = True
                else:
                    score = 1000 + area_penalty + aspect_penalty * 5.0
                    if not found_within_limit and score < best_score:
                        best_score = score
                        best_w = w
                        best_h = h
            
    total = best_w * best_h
    if "4:3" in name: 
        default_h, default_w = best_h, best_w

    h_A4, w_A4 = best_h * PAINTED_H_A4, best_w * PAINTED_W_A4
    h_A3, w_A3 = best_h * PAINTED_H_A3, best_w * PAINTED_W_A3
    h_B5, w_B5 = best_h * PAINTED_H_B5, best_w * PAINTED_W_B5
    h_A5, w_A5 = best_h * PAINTED_H_A5, best_w * PAINTED_W_A5
    
    with cols[i % 2]:
        st.markdown(f"**▼ {name}** ⇒ 【縦 **{best_h}** 枚 × 横 **{best_w}** 枚】 (計 {total} 枚 / 予備 +{total - target_area}枚)")
        st.caption(f"[A3] 縦 約 {h_A3:.1f}m×横 約 {w_A3:.1f}m / [A4] 縦 約 {h_A4:.1f}m×横 約 {w_A4:.1f}m<br>[B5] 縦 約 {h_B5:.1f}m×横 約 {w_B5:.1f}m / [A5] 縦 約 {h_A5:.1f}m×横 約 {w_A5:.1f}m", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 3. 枠の決定と画像アップロード
# ==========================================
st.subheader("🖼️ ステップ2：最大の枠の決定と画像の選択")
st.write("上のリストを参考に「最大の枠」を入力し、画像をアップロードしてください。（※画像の縦横比を100%維持するため、不要な用紙は自動で削られます）")

col1, col2 = st.columns(2)
with col1:
    max_sheets_h = st.number_input("縦の枚数", min_value=1, max_value=200, value=default_h)
with col2:
    max_sheets_w = st.number_input("横の枚数", min_value=1, max_value=200, value=default_w)

uploaded_file = st.file_uploader("変換する画像ファイルを選択", type=['png', 'jpg', 'jpeg'])

# ==========================================
# 4. メイン処理（画像アップロード後）
# ==========================================
if uploaded_file is not None:
    with st.spinner('画像を処理し、PDF設計図を生成しています...（数十秒かかります）'):
        img = Image.open(uploaded_file).convert("RGB")
        img_w, img_h = img.size
        img_aspect = img_h / img_w
        
        max_pixels_w = max_sheets_w * CELLS_W
        max_pixels_h = max_sheets_h * CELLS_H
        
        # 枠の物理サイズ（色塗り部分のみ）を基準に比率計算
        frame_physical_w = max_sheets_w * PAINTED_W_A4
        frame_physical_h = max_sheets_h * PAINTED_H_A4
        frame_physical_aspect = frame_physical_h / frame_physical_w

        if img_aspect > frame_physical_aspect:
            target_physical_h = frame_physical_h
            target_physical_w = frame_physical_h / img_aspect
        else:
            target_physical_w = frame_physical_w
            target_physical_h = frame_physical_w * img_aspect

        target_w_pixels = int(max_pixels_w * (target_physical_w / frame_physical_w))
        target_h_pixels = int(max_pixels_h * (target_physical_h / frame_physical_h))

        target_w_pixels = max(1, target_w_pixels)
        target_h_pixels = max(1, target_h_pixels)

        actual_sheets_w = math.ceil(target_w_pixels / CELLS_W)
        actual_sheets_h = math.ceil(target_h_pixels / CELLS_H)

        img_resized = img.resize((target_w_pixels, target_h_pixels), Image.Resampling.LANCZOS)
        canvas_w = actual_sheets_w * CELLS_W
        canvas_h = actual_sheets_h * CELLS_H
        base_img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        base_img.paste(img_resized, (0, 0))

        total_sheets = actual_sheets_w * actual_sheets_h
        h_A4, w_A4 = actual_sheets_h * PAINTED_H_A4, actual_sheets_w * PAINTED_W_A4
        h_A3, w_A3 = actual_sheets_h * PAINTED_H_A3, actual_sheets_w * PAINTED_W_A3
        h_B5, w_B5 = actual_sheets_h * PAINTED_H_B5, actual_sheets_w * PAINTED_W_B5
        h_A5, w_A5 = actual_sheets_h * PAINTED_H_A5, actual_sheets_w * PAINTED_W_A5

        st.markdown("---")
        st.subheader("✅ 処理完了！ 完成データ")
        
        res_col1, res_col2 = st.columns([1, 1])
        with res_col1:
            st.success(f"**最終的な用紙数 : 縦 {actual_sheets_h} 枚 × 横 {actual_sheets_w} 枚 (計 {total_sheets} 枚)**")
            if actual_sheets_h != max_sheets_h or actual_sheets_w != max_sheets_w:
                st.warning("※元の縦横比を維持するため、枠から不要な用紙を自動で削りました。")
            st.write(f"・総マス目数 : {target_h_pixels * target_w_pixels:,} マス")
            st.write("※以下の物理サイズは、周囲の余白をカットして連結させた際の寸法です。")
            st.write(f"・[ A3 で印刷 ] : 縦 約 {h_A3:.2f} m × 横 約 {w_A3:.2f} m （特大化）")
            st.write(f"・[ A4 で印刷 ] : 縦 約 {h_A4:.2f} m × 横 約 {w_A4:.2f} m （基準）")
            st.write(f"・[ B5 で印刷 ] : 縦 約 {h_B5:.2f} m × 横 約 {w_B5:.2f} m （少し縮小）")
            st.write(f"・[ A5 で印刷 ] : 縦 約 {h_A5:.2f} m × 横 約 {w_A5:.2f} m （A4用紙に2in1で割付印刷）")
            
        pal_img = Image.new("P", (1, 1))
        flat_palette = []
        for color_data in SELECTED_PALETTE:
            flat_palette.extend(color_data["rgb"])
        flat_palette.extend([0] * (768 - len(flat_palette)))
        pal_img.putpalette(flat_palette)

        img_dithered = base_img.quantize(palette=pal_img, dither=Image.Dither.FLOYDSTEINBERG)
        preview_img = img_dithered.crop((0, 0, target_w_pixels, target_h_pixels)).convert("RGB")
        
        with res_col2:
            st.image(preview_img, caption="完成予想プレビュー", use_column_width=True)

        font_path = "ipaexg.ttf"
        if not os.path.exists(font_path):
            zip_url = "https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip"
            urllib.request.urlretrieve(zip_url, "ipaexfont.zip")
            with zipfile.ZipFile("ipaexfont.zip", 'r') as zip_ref:
                zip_ref.extract("IPAexfont00401/ipaexg.ttf")
            os.rename("IPAexfont00401/ipaexg.ttf", font_path)
        pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))

        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))
        a4_w, a4_h = landscape(A4)

        margin_x = 15 * mm
        margin_y = 15 * mm
        header_space = 15 * mm
        draw_area_w = a4_w - (margin_x * 2)
        draw_area_h = a4_h - (margin_y * 2) - header_space
        cell_w = draw_area_w / CELLS_W
        cell_h = draw_area_h / CELLS_H

        for y in range(actual_sheets_h):
            for x in range(actual_sheets_w):
                c.setFont('JapaneseFont', 12)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(margin_x, a4_h - margin_y, f"【 縦 {y+1} 行目 / 横 {x+1} 列目 】")

                for cy in range(CELLS_H):
                    for cx in range(CELLS_W):
                        global_x = x * CELLS_W + cx
                        global_y = y * CELLS_H + cy
                        
                        if global_x >= target_w_pixels or global_y >= target_h_pixels:
                            char = "白"
                        else:
                            idx = img_dithered.getpixel((global_x, global_y))
                            char = SELECTED_PALETTE[idx]["char"]
                        
                        px = margin_x + cx * cell_w
                        py = a4_h - margin_y - header_space - (cy + 1) * cell_h

                        c.setStrokeColorRGB(0.7, 0.7, 0.7) 
                        c.setLineWidth(0.5)
                        c.rect(px, py, cell_w, cell_h, fill=0)

                        if char != "白":
                            char_len = len(char)
                            font_size = min(cell_w, cell_h) * (0.50 if char_len == 1 else 0.40)
                            c.setFont('JapaneseFont', font_size)
                            text_width = c.stringWidth(char, 'JapaneseFont', font_size)
                            tx = px + (cell_w - text_width) / 2.0
                            ty = py + (cell_h - font_size) / 2.0 + (font_size * 0.15)
                            c.setFillColorRGB(0.6, 0.6, 0.6)
                            c.drawString(tx, ty, char)
                c.showPage()
        c.save()
        pdf_bytes = pdf_buffer.getvalue()

        st.markdown("### 📥 設計図のダウンロード")
        st.download_button(
            label="📄 PDFファイルをダウンロード",
            data=pdf_bytes,
            file_name=f"mosaic_blueprint_H{actual_sheets_h}xW{actual_sheets_w}.pdf",
            mime="application/pdf"
        )
