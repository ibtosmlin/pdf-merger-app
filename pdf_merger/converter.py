from pathlib import Path

import pythoncom
import win32com.client


def convert_docx_to_pdf(input_path: Path, output_path: Path) -> None:
    """
    WordファイルをPDFに変換する。

    Parameters:
        input_path (Path): 入力Wordファイルのパス
        output_path (Path): 出力PDFファイルのパス
    """
    pythoncom.CoInitialize()
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(input_path.resolve()))
        doc.SaveAs(str(output_path.resolve()), FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
    finally:
        pythoncom.CoUninitialize()


def convert_pptx_to_pdf(input_path: Path, output_path: Path) -> None:
    """
    PowerPointファイルをPDFに変換する。

    Parameters:
        input_path (Path): 入力PowerPointファイルのパス
        output_path (Path): 出力PDFファイルのパス
    """
    pythoncom.CoInitialize()
    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = False
        presentation = powerpoint.Presentations.Open(
            str(input_path.resolve()), WithWindow=False
        )
        presentation.SaveAs(str(output_path.resolve()), FileFormat=32)  # 32 = PDF
        presentation.Close()
        powerpoint.Quit()
    finally:
        pythoncom.CoUninitialize()


def convert_xlsx_to_pdf(input_path: Path, output_path: Path) -> None:
    """
    Excelファイルの中でページ設定（PrintArea）があるシートのみをPDFに変換する。

    Parameters:
        input_path (Path): 入力Excelファイルのパス
        output_path (Path): 出力PDFファイルのパス
    """
    pythoncom.CoInitialize()
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        wb = excel.Workbooks.Open(str(input_path.resolve()))

        sheets_to_export = [
            sheet.Name for sheet in wb.Sheets if sheet.PageSetup.PrintArea
        ]

        if sheets_to_export:
            wb.Worksheets(sheets_to_export).Select()
            wb.ActiveSheet.ExportAsFixedFormat(0, str(output_path.resolve()))
        else:
            raise ValueError("ページ設定のあるシートが見つかりませんでした。")

        wb.Close(False)
        excel.Quit()
    finally:
        pythoncom.CoUninitialize()


def convert_to_pdf(input_path: Path, output_path: Path) -> bool:
    """
    拡張子に応じて適切なアプリケーションでPDF変換を行う。

    Parameters:
        input_path (Path): 入力ファイルのパス
        output_path (Path): 出力PDFファイルのパス

    Returns:
        bool: 変換成功なら True、未対応形式なら False
    """
    ext = input_path.suffix.lower()

    if ext == ".docx":
        convert_docx_to_pdf(input_path, output_path)
    elif ext == ".xlsx":
        convert_xlsx_to_pdf(input_path, output_path)
    elif ext == ".pptx":
        convert_pptx_to_pdf(input_path, output_path)
    else:
        return False

    return True
