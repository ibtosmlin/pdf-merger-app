import os
from datetime import datetime
from pathlib import Path

import streamlit as st

import pdf_merger  # PDF変換・サムネイル抽出・ページ結合ロジック
from pdf_merger.pagedata import create_blank_page

# 📁 作業ディレクトリの準備
CWD = Path(__file__).parent / ".work"
MASTER_DIR = CWD / "master"
IMG_DIR = CWD / "images"
EDITED_DIR = CWD / "edited"
for d in [MASTER_DIR, IMG_DIR, EDITED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 🖥️ ページ設定
st.set_page_config(page_title="PDF Merger", layout="wide")
st.title("📄 PDF Merger")
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
    for DIR in [MASTER_DIR, IMG_DIR, EDITED_DIR]:
        for path in DIR.glob("*.*"):
            path.unlink()

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

    page_data_list = pdf_merger.extract_thumbnails(MASTER_DIR, IMG_DIR)
    st.session_state.page_data_list = page_data_list
    st.session_state.selected_pages = []


# 🧩 グループ化関数
def group_by_file(page_data_list):
    groups = {}
    for page in page_data_list:
        groups.setdefault(page.file, []).append(page)
    return groups


# 🧠 UI表示と並び替え
if "page_data_list" in st.session_state:
    st.write("---")
    groups = group_by_file(st.session_state.page_data_list)

    st.subheader("📁 ファイル別ページ一覧")
    for file, pages in groups.items():
        # 🔲 ラベル・全選択・全削除を横並びに表示
        label_col, select_col = st.columns([6, 1])
        with label_col:
            expander = st.expander(f"📄 {file}", expanded=True)
        with select_col:
            if st.button("⭐ 全選択", key=f"select-all-{file}"):
                for page in pages:
                    if page not in st.session_state.selected_pages:
                        st.session_state.selected_pages.append(page)
                st.rerun()
            if st.button("🗑️ 全削除", key=f"delete-all-{file}"):
                st.session_state.selected_pages = [
                    p for p in st.session_state.selected_pages if p.file != file
                ]
                st.rerun()

        # 🖼️ 列表示
        colnum = 6
        with expander:
            cols = st.columns(colnum)
            for i, page in enumerate(pages):
                with cols[i % colnum]:
                    st.image(
                        page.thumbnail_path,
                        caption=f"p{page.page_index}",
                        width="stretch",
                    )
                    if st.button("⭐ 選択", key=f"select-{file}-{i}"):
                        if page not in st.session_state.selected_pages:
                            st.session_state.selected_pages.append(page)
                            st.rerun()

    st.write("---")

    st.subheader("⭐ 選択されたページ")

    if st.button("📎 選択ページでPDF結合"):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"pdf_merge_app_{timestamp}.pdf"
        output_path = EDITED_DIR / filename
        success = pdf_merger.merge_pages(
            MASTER_DIR, st.session_state.selected_pages, output_path
        )
        if success:
            st.success(f"✅ 結合PDFを保存しました: {output_path.name}")
            st.download_button(
                label="📥 ダウンロード",
                data=output_path.read_bytes(),
                file_name=output_path.name,
                mime="application/pdf",
            )
        else:
            st.error("❌ PDF結合に失敗しました")
    st.write("---")

    if st.session_state.selected_pages:
        cols = st.columns(2)
        for i, page in enumerate(st.session_state.selected_pages):
            if i % 2 == 0:
                cols = st.columns(2)
            with cols[i % 2]:
                st.image(
                    page.thumbnail_path,
                    caption=f"{page.file} - p{page.page_index}",
                    width="stretch",
                )

                _, col1, col2, col3, col4, col5, _ = st.columns([2, 1, 1, 1, 1, 1, 2])
                with col1:
                    if st.button("⬆️", key=f"up-{i}") and i > 0:
                        (
                            st.session_state.selected_pages[i],
                            st.session_state.selected_pages[i - 1],
                        ) = (
                            st.session_state.selected_pages[i - 1],
                            st.session_state.selected_pages[i],
                        )
                        st.rerun()
                with col2:
                    if (
                        st.button("⬇️", key=f"down-{i}")
                        and i < len(st.session_state.selected_pages) - 1
                    ):
                        (
                            st.session_state.selected_pages[i],
                            st.session_state.selected_pages[i + 1],
                        ) = (
                            st.session_state.selected_pages[i + 1],
                            st.session_state.selected_pages[i],
                        )
                        st.rerun()
                with col3:
                    if st.button("❌", key=f"remove-{i}"):
                        st.session_state.selected_pages.pop(i)
                        st.rerun()

                with col4:
                    if st.button("⤵️", key=f"rotate-{i}"):
                        page.update_thumbnail()
                        st.rerun()

                with col5:
                    if st.button("➕ ", key=f"insert-blank-after-{i}"):
                        blank_page = create_blank_page()
                        st.session_state.selected_pages.insert(i + 1, blank_page)
                        st.rerun()

            if i % 2:
                st.write("")

        st.write("---")

        if st.button("📎 選択ページでPDF結合 "):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"pdf_merge_app_{timestamp}.pdf"
            output_path = EDITED_DIR / filename
            success = pdf_merger.merge_pages(
                MASTER_DIR, st.session_state.selected_pages, output_path
            )
            if success:
                st.success(f"✅ 結合PDFを保存しました: {output_path.name}")
                st.download_button(
                    label="📥 ダウンロード",
                    data=output_path.read_bytes(),
                    file_name=output_path.name,
                    mime="application/pdf",
                )
            else:
                st.error("❌ PDF結合に失敗しました")
