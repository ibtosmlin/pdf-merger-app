import os
from pathlib import Path
from datetime import datetime

import streamlit as st
from streamlit_sortables import sort_items

import pdf_merger  # PDF変換・サムネイル抽出・ページ結合ロジック

# 📁 作業ディレクトリの準備
CWD = Path(__file__).parent / ".work"
MASTER_DIR = CWD / "master"
IMG_DIR = CWD / "images"
EDITED_DIR = CWD / "edited"
for d in [MASTER_DIR, IMG_DIR, EDITED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 🖥️ ページ設定
st.set_page_config(page_title="PDF-merger", layout="wide")
st.title("📄 PDF-merger")
st.write("---")

# 📂 ファイルアップロード
uploaded_files = st.file_uploader(
    label="📂 ファイルをアップロード（複数可）",
    type=["pdf", "xlsx", "docx", "pptx"],
    accept_multiple_files=True,
)

# 📄 PDF化ボタン
go_pdf = st.button("📄 PDF化") if uploaded_files else False

# 🔄 PDF変換処理
if uploaded_files and go_pdf:
    # 既存ファイル削除
    for DIR in [MASTER_DIR, IMG_DIR, EDITED_DIR]:
        for path in DIR.glob("*.*"):
            path.unlink()

    # アップロードファイルの処理
    for i, uploaded_file in enumerate(uploaded_files):
        filename = os.path.basename(uploaded_file.name)
        ext = Path(filename).suffix.lower()
        temp_path = MASTER_DIR / filename
        temp_path.write_bytes(uploaded_file.getbuffer())

        try:
            pdf_name = f"M{i:02}_{Path(filename).stem}.pdf"
            pdf_path = MASTER_DIR / pdf_name

            if ext == ".pdf":
                temp_path.rename(pdf_path)
                st.success(f"✅ PDFファイル {filename} を保存しました → {pdf_name}")
            else:
                if not pdf_merger.convert_to_pdf(temp_path, pdf_path):
                    st.warning(f"⚠️ 未対応の形式: {filename}")
                    continue
                st.success(f"📄 {filename} を PDF に変換して保存しました → {pdf_name}")
                temp_path.unlink()
        except Exception as e:
            st.error(f"❌ {filename} の変換に失敗しました: {e}")


    # サムネイル画像の初期化
    for f in IMG_DIR.glob("*.*"):
        f.unlink()

    # サムネイル生成とセッション保存
    page_data_list = pdf_merger.extract_thumbnails(MASTER_DIR, IMG_DIR)
    st.session_state.page_data_list = page_data_list
    st.session_state.initialized = False  # 初期化フラグ

# 🧩 コンテナ初期化関数
def initialize_containers(page_data_list):
    file_groups = {}
    label_to_page = {}
    containers = []

    for page in page_data_list:
        file_groups.setdefault(page.file, []).append(page)

    for file, pages in file_groups.items():
        labels = []
        for page in pages:
            label = f"{file} - p{page.page_index}"
            labels.append(label)
            label_to_page[label] = page
        containers.append({"header": f"📄 {file}", "items": labels})

    containers.append({"header": "⭐ selected", "items": []})
    return containers, label_to_page

# 🧠 並び替えUIの表示と処理
if "page_data_list" in st.session_state:
    st.write("---")
    if not st.session_state.get("initialized", False):
        containers, label_to_page = initialize_containers(st.session_state.page_data_list)
        st.session_state.sorted_containers = containers
        st.session_state.label_to_page = label_to_page
        st.session_state.initialized = True

    # 並び替えUIの描画
    new_sorted = sort_items(
        st.session_state.sorted_containers,
        multi_containers=True,
        key="sortable-ui"
    )

    # ⭐ selected コンテナが消えた場合は復元
    headers = [c["header"] for c in new_sorted]
    if "⭐ selected" not in headers:
        new_sorted.append({"header": "⭐ selected", "items": []})

    # 選択されたページを抽出
    sorted_pages = []
    for container in new_sorted:
        if container["header"] == "⭐ selected":
            for label in container["items"]:
                page = st.session_state.label_to_page.get(label)
                if page:
                    sorted_pages.append(page)

    # セッションに保存
    st.session_state.sorted_containers = new_sorted

    # 🖼️ サムネイル表示（4列レイアウト）
    cols = st.columns(4)
    for i, page in enumerate(sorted_pages):
        with cols[i % 4]:
            st.image(
                page.thumbnail_path,
                caption=f"{page.file} - p{page.page_index}",
                width="stretch"
            )
    st.write("---")

    # 📎 PDF結合ボタンと保存・ダウンロード
    if st.button("📎 選択ページでPDF結合"):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"pdf_merge_app_{timestamp}.pdf"
        output_path = EDITED_DIR / filename

        success = pdf_merger.merge_pages(MASTER_DIR, sorted_pages, output_path)
        if success:
            st.success(f"✅ 結合PDFを保存しました: {output_path.name}")
            st.download_button(
                label="📥 ダウンロード",
                data=output_path.read_bytes(),
                file_name=output_path.name,
                mime="application/pdf"
            )
        else:
            st.error("❌ PDF結合に失敗しました")