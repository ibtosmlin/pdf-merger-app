from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

CWD = Path(__file__).parent


@dataclass
class PageData:
    file: str
    thumbnail_path: Path
    source_pdf_path: Path
    page_index: int = 0
    keep: bool = True
    order: int = 0
    rotation: int = 0  # 回転角度（0, 90, 180, 270）
    is_blank: bool = False

    def update_thumbnail(self) -> None:
        """
        指定された PageData に基づいてサムネイル画像を再生成する。

        Parameters:
            page_data (PageData): 回転角度などを含むページ情報
        """
        self.rotation = (self.rotation + 90) % 360
        if self.is_blank:
            self.thumbnail_path = str(CWD / f"blank_page_{self.rotation % 180}.png")
            return
        try:
            with fitz.open(self.source_pdf_path) as doc:
                page = doc.load_page(self.page_index)
                matrix = fitz.Matrix(0.5, 0.5).prerotate(self.rotation)
                pix = page.get_pixmap(matrix=matrix)
                pix.save(str(self.thumbnail_path))
        except Exception as e:
            print(f"❌ サムネイル更新エラー: {self.file} - p{self.page_index}: {e}")


def extract_thumbnails(pdf_dir: Path, img_dir: Path) -> list[PageData]:
    page_data_list = []

    for pdf_path in pdf_dir.glob("*.pdf"):
        with fitz.open(pdf_path) as doc:
            for i in range(doc.page_count):
                page = doc.load_page(i)
                rotation_matrix = fitz.Matrix(0.5, 0.5).prerotate(0)  # 初期は0度
                pix = page.get_pixmap(matrix=rotation_matrix)

                thumb_name = f"{pdf_path.stem}_p{i:03}.jpg"
                thumb_path = img_dir / thumb_name
                pix.save(str(thumb_path))

                page_data_list.append(
                    PageData(
                        file=pdf_path.name,
                        thumbnail_path=thumb_path,
                        page_index=i,
                        keep=True,
                        order=i,
                        source_pdf_path=pdf_path,
                        rotation=0,
                    )
                )

    return page_data_list


def merge_pages(
    master_dir: Path, page_data_list: list[PageData], output_path: Path
) -> bool:
    merged_doc = fitz.open()
    file_cache = {}

    try:
        for page_data in page_data_list:
            # if getattr(page_data, "is_blank", False):
            if page_data.is_blank:
                # 空白ページ（A4サイズ）
                width = 595
                height = 842
                if page_data.rotation % 180:
                    width, height = height, width
                merged_doc.new_page(width=width, height=height)
                continue

            pdf_path = master_dir / page_data.file
            if pdf_path not in file_cache:
                file_cache[pdf_path] = fitz.open(pdf_path)
            src_doc = file_cache[pdf_path]
            page_index = page_data.page_index

            if 0 <= page_index < src_doc.page_count:
                page = src_doc.load_page(page_index)
                if page_data.rotation != 0:
                    rotation_matrix = fitz.Matrix(1, 1).prerotate(page_data.rotation)
                    pix = page.get_pixmap(matrix=rotation_matrix)
                    img_pdf = fitz.open()
                    rect = fitz.Rect(0, 0, pix.width, pix.height)
                    img_page = img_pdf.new_page(width=rect.width, height=rect.height)
                    img_page.insert_image(rect, pixmap=pix)
                    merged_doc.insert_pdf(img_pdf)
                    img_pdf.close()
                else:
                    merged_doc.insert_pdf(
                        src_doc, from_page=page_index, to_page=page_index
                    )
            else:
                print(f"⚠️ ページ番号が範囲外: {page_data.file} - p{page_index}")

        merged_doc.save(output_path)
        merged_doc.close()
        return True

    except Exception as e:
        print(f"❌ PDF結合エラー: {e}")
        return False


def create_blank_page():
    blank_page = PageData(
        file="__blank__",
        page_index=0,
        thumbnail_path=str(CWD / "blank_page_0.png"),
        source_pdf_path=CWD,
        rotation=0,
        is_blank=True,
    )
    return blank_page
