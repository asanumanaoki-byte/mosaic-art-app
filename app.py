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
target_area = st.sidebar.number_input("1. 目標とする総枚数（全校生徒数など）", min_value=1, value=553, step=10)

# A4とA5印刷時のマス目の物理サイズ目安を併記
cell_options = {
    "パターン1（横16×縦10 / A4:約1.7cm角, A5:約1.2cm角）": (16, 10),
    "パターン2（横21×縦13 / A4:約1.3cm角, A5:約9mm角）": (21, 13),
    "パターン3（横26×縦16 / A4:約1cm角, A5:約7mm角）": (26, 16),
    "パターン4（横32×縦20 / A4:約8mm角, A5:約6mm角）": (32, 20),
    "パターン5（横42×縦26 / A4:約6mm角, A5:約4mm角）": (42, 26),
    "パターン6（横52×縦32 / A4:約5mm角, A5:約3.5mm角）": (52, 32)
}
cell_choice = st.sidebar.selectbox("2. マス目の細かさ", list(cell_options.keys()), index=2)
CELLS_W, CELLS_H = cell_options[cell_choice]

palette_options = {
    "クーピー12色（標準）": [
        {"name": "あか", "char": "赤", "rgb": (230, 0, 18)}, {"name": "だいだい", "char": "橙", "rgb": (243, 152, 0)},
        {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)}, {"name": "きみどり", "char": "黄緑", "rgb": (143, 195, 31)},
        {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)}, {"name": "みずいろ", "char": "水色", "rgb": (0, 160, 233)},
        {"name": "あお", "char": "青", "rgb": (0, 104, 183)}, {"name": "むらさき", "char": "紫", "rgb": (146, 7, 131)},
        {"name": "ももいろ", "char": "桃色", "rgb": (228, 0, 127)}, {"name": "ちゃいろ", "char": "茶色", "rgb": (143, 84, 44)},
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ],
    "プロッキー12色": [
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "むらさき", "char": "紫", "rgb": (146, 7, 131)},
        {"name": "あお", "char": "青", "rgb": (0, 104, 183)}, {"name": "みずいろ", "char": "水色", "rgb": (0, 160, 233)},
        {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)}, {"name": "きみどり", "char": "黄緑", "rgb": (143, 195, 31)},
        {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)}, {"name": "だいだい", "char": "橙", "rgb": (243, 152, 0)},
        {"name": "ソフトピンク", "char": "桃色", "rgb": (255, 153, 204)}, {"name": "あか", "char": "赤", "rgb": (230, 0, 18)},
        {"name": "おうどいろ", "char": "黄土", "rgb": (204, 153, 51)}, {"name": "ちゃいろ", "char": "茶色", "rgb": (143, 84, 44)},
        {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ],
    "プロッキー10色": [
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "あお", "char": "青", "rgb": (0, 104, 183)},
        {"name": "みずいろ", "char": "水色", "rgb": (0, 160, 233)}, {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)},
        {"name": "きみどり", "char": "黄緑", "rgb": (143, 195, 31)}, {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)},
        {"name": "だいだい", "char": "橙", "rgb": (243, 152, 0)}, {"name": "あか", "char": "赤", "rgb": (230, 0, 18)},
        {"name": "ソフトピンク", "char": "桃色", "rgb": (255, 153, 204)}, {"name": "むらさき", "char": "紫", "rgb": (146, 7, 131)},
        {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ],
    "プロッキー8色": [
        {"name": "くろ", "char": "黒", "rgb": (0, 0, 0)}, {"name": "あお", "char": "青", "rgb": (0, 104, 183)},
        {"name": "みずいろ", "char": "水色", "rgb": (0, 160, 233)}, {"name": "みどり", "char": "緑", "rgb": (0, 153, 68)},
        {"name": "きいろ", "char": "黄", "rgb": (255, 236, 0)}, {"name": "ソフトピンク", "char": "桃色", "rgb": (255, 153, 204)},
        {"name": "あか", "char": "赤", "rgb": (230, 0, 18)}, {"name": "ちゃいろ", "char": "茶色", "rgb": (143, 84, 44)},
        {"name": "しろ", "char": "白", "rgb": (255, 255, 255)}
    ]
}
palette_choice = st.sidebar.selectbox("3. 使用する画材", list(palette_options.keys()))
SELECTED_PALETTE = palette_options[palette_choice]

# ==========================================
# 2. 事前ガイド（推奨サイズ計算）
# ==========================================
st.subheader("💡 ステップ1：代表的な画像比率と最適な用紙枚数")
st.info(f"目標枚数（{target_area} 枚）を**必ず上回る最小の組み合わせ**を計算しました。\n\n※PDF出力後、印刷設定で用紙サイズ（A3/A4/B5/A5等）を変更するだけで全体の大きさを調整できます。")

ratios = {
    "16:9 (動画・スマホ横)": 16/9,
    " 3:2 (一眼レフ写真)": 3/2,
    " 4:3 (デジカメ・iPad)": 4/3,
    " 1:1 (正方形など)": 1/1
}

default_w, default_h = 28, 20
cols = st.columns(2)

for i, (name, ratio) in enumerate(ratios.items()):
    R = ratio * (CELLS_H / CELLS_W)
    base_h = math.sqrt(target_area / R)
    best_w, best_h = 0, 0
    min_total = float('inf')
    
    for h in range(max(1, math.floor(base_h) - 5), math.ceil(base_h) + 5):
        w = round(R * h)
        total = w * h
        if total >= target_area and total < min_total:
            min_total = total
            best_w = w
            best_h = h
            
    total = best_w * best_h
    if "4:3" in name: 
        default_w, default_h = best_w, best_h

    w_A4, h_A4 = best_w * 0.297, best_h * 0.210
    w_A3, h_A3 = best_w * 0.420, best_h * 0.297
    w_B5, h_B5 = best_w * 0.257, best_h * 0.182
    w_A5, h_A5 = best_w * 0.210, best_h * 0.148
    
    with cols[i % 2]:
        st.markdown(f"**▼ {name}** ⇒ 【横 **{best_w}** 枚 × 縦 **{best_h}** 枚】 (計 {total} 枚 / 予備 +{total - target_area}枚)")
        st.caption(f"[A3] 約 {w_A3:.1f}m×{h_A3:.1f}m / [A4] 約 {w_A4:.1f}m×{h_A4:.1f}m<br>[B5] 約 {w_B5:.1f}m×{h_B5:.1f}m / [A5] 約 {w_A5:.1f}m×{h_A5:.1f}m", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 3. 枠の決定と画像アップロード
# ==========================================
st.subheader("🖼️ ステップ2：最大の枠の決定と画像の選択")
st.write("上のリストを参考に「最大の枠」を入力し、画像をアップロードしてください。（※画像の縦横比を100%維持するため、不要な用紙は自動で削られます）")

col1, col2 = st.columns(2)
with col1:
    max_sheets_w = st.number_input("横の枚数", min_value=1, max_value=200, value=default_w)
with col2:
    max_sheets_h = st.number_input("縦の枚数", min_value=1, max_value=200, value=default_h)

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
        frame_aspect = max_pixels_h / max_pixels_w

        if img_aspect > frame_aspect:
            target_h_pixels = max_pixels_h
            target_w_pixels = int(max_pixels_h / img_aspect)
        else:
            target_w_pixels = max_pixels_w
            target_h_pixels = int(max_pixels_w * img_aspect)

        actual_sheets_w = math.ceil(target_w_pixels / CELLS_W)
        actual_sheets_h = math.ceil(target_h_pixels / CELLS_H)

        img_resized = img.resize((target_w_pixels, target_h_pixels), Image.Resampling.LANCZOS)
        canvas_w = actual_sheets_w * CELLS_W
        canvas_h = actual_sheets_h * CELLS_H
        base_img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        base_img.paste(img_resized, (0, 0))

        total_sheets = actual_sheets_w * actual_sheets_h
        w_A4, h_A4 = actual_sheets_w * 0.297, actual_sheets_h * 0.210
        w_A3, h_A3 = actual_sheets_w * 0.420, actual_sheets_h * 0.297
        w_B5, h_B5 = actual_sheets_w * 0.257, actual_sheets_h * 0.182
        w_A5, h_A5 = actual_sheets_w * 0.210, actual_sheets_h * 0.148

        # プレビュー表示
        st.markdown("---")
        st.subheader("✅ 処理完了！ 完成データ")
        
        res_col1, res_col2 = st.columns([1, 1])
        with res_col1:
            st.success(f"**最終的な用紙数 : 横 {actual_sheets_w} 枚 × 縦 {actual_sheets_h} 枚 (計 {total_sheets} 枚)**")
            if actual_sheets_w != max_sheets_w or actual_sheets_h != max_sheets_h:
                st.warning("※元の縦横比を維持するため、枠から不要な用紙を自動で削りました。")
            st.write(f"・総マス目数 : {target_w_pixels * target_h_pixels:,} マス")
            st.write(f"・[ A3 で印刷 ] : 横 約 {w_A3:.2f} m × 高さ 約 {h_A3:.2f} m （特大化）")
            st.write(f"・[ A4 で印刷 ] : 横 約 {w_A4:.2f} m × 高さ 約 {h_A4:.2f} m （基準）")
            st.write(f"・[ B5 で印刷 ] : 横 約 {w_B5:.2f} m × 高さ 約 {h_B5:.2f} m （少し縮小）")
            st.write(f"・[ A5 で印刷 ] : 横 約 {w_A5:.2f} m × 高さ 約 {h_A5:.2f} m （A4用紙に2in1で割付印刷）")
            
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

        # PDF生成
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
                c.drawString(margin_x, a4_h - margin_y, f"【 横 {x+1} 列目 / 縦 {y+1} 行目 】")

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
            file_name=f"mosaic_blueprint_W{actual_sheets_w}xH{actual_sheets_h}.pdf",
            mime="application/pdf"
        )
