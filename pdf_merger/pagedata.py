from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class PageData:
    file: str  # 元PDFファイル名
    page_index: int  # ページ番号（0始まり）
    thumbnail_path: Path  # サムネイル画像の保存先
    keep: bool  # マージ対象にするか
    order: int  # マージ順
    source_pdf_path: Path  # 元PDFファイルの絶対パス


def extract_thumbnails(pdf_dir: Path, img_dir: Path) -> list[PageData]:
    """
    指定フォルダ内のPDFから各ページのサムネイルを生成し、PageDataとして返す。

    Parameters:
        pdf_dir (Path): PDFファイルが格納されたディレクトリ
        img_dir (Path): サムネイル画像の保存先ディレクトリ

    Returns:
        list[PageData]: 各ページの情報を含むリスト
    """
    page_data_list = []

    for pdf_path in pdf_dir.glob("*.pdf"):
        doc = fitz.open(pdf_path)

        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # 軽量化のため縮小

            thumb_name = f"{pdf_path.stem}_p{i:03}.jpg"
            thumb_path = img_dir / thumb_name
            pix.save(str(thumb_path))

            page_data_list.append(
                PageData(
                    file=pdf_path.name,
                    page_index=i,
                    thumbnail_path=thumb_path,
                    keep=True,
                    order=i,
                    source_pdf_path=pdf_path,
                )
            )

        doc.close()

    return page_data_list


def merge_pages(
    master_dir: Path, page_data_list: list[PageData], output_path: Path
) -> bool:
    """
    指定されたページ順にPDFを結合して保存する。

    Parameters:
        master_dir (Path): 元PDFファイルの格納ディレクトリ
        page_data_list (list[PageData]): 結合対象のページ情報リスト
        output_path (Path): 出力PDFファイルの保存先

    Returns:
        bool: 結合成功なら True、失敗なら False
    """
    merged_doc = fitz.open()
    file_cache = {}

    try:
        for page_data in page_data_list:
            pdf_path = master_dir / page_data.file

            if pdf_path not in file_cache:
                file_cache[pdf_path] = fitz.open(pdf_path)

            src_doc = file_cache[pdf_path]
            page_index = page_data.page_index

            if 0 <= page_index < src_doc.page_count:
                merged_doc.insert_pdf(src_doc, from_page=page_index, to_page=page_index)
            else:
                print(f"⚠️ ページ番号が範囲外: {page_data.file} - p{page_index}")

        merged_doc.save(output_path)
        merged_doc.close()
        return True

    except Exception as e:
        print(f"❌ PDF結合エラー: {e}")
        return False
