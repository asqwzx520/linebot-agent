"""
資料分析模組 — 解析 Excel / CSV，生成統計摘要供 Gemini 分析。
"""

import io
from typing import Tuple


def analyze_file(file_bytes: bytes, filename: str) -> Tuple[str, int, int]:
    """
    解析 Excel 或 CSV 檔案，回傳 (摘要文字, 資料筆數, 欄位數)。

    Args:
        file_bytes: 檔案二進位內容
        filename:   原始檔名（用於判斷格式）

    Returns:
        (summary_text, row_count, col_count)

    Raises:
        ValueError: 不支援的檔案格式
        Exception:  pandas 解析失敗
    """
    import pandas as pd

    fname = filename.lower()

    # ── 讀取檔案 ──────────────────────────────────────────────────────────────
    if fname.endswith(".csv"):
        df = _read_csv_auto_encoding(file_bytes)
    elif fname.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"不支援的格式：{filename}（僅支援 .xlsx / .xls / .csv）")

    rows, cols = df.shape

    # ── 欄位清單 ──────────────────────────────────────────────────────────────
    col_lines = []
    for col in df.columns:
        dtype     = str(df[col].dtype)
        null_cnt  = int(df[col].isnull().sum())
        null_info = f"，{null_cnt} 個空值" if null_cnt > 0 else ""
        col_lines.append(f"  • {col} [{dtype}]{null_info}")

    # ── 數值欄位統計（最多 10 欄）────────────────────────────────────────────
    numeric_df  = df.select_dtypes(include="number")
    stats_lines = []
    for col in list(numeric_df.columns)[:10]:
        s = numeric_df[col].dropna()
        if len(s) == 0:
            continue
        stats_lines.append(
            f"  • {col}: 平均={s.mean():.2f}  最大={s.max():.2f}"
            f"  最小={s.min():.2f}  總和={s.sum():.2f}"
        )

    # ── 文字欄位：前幾個唯一值 ────────────────────────────────────────────────
    cat_lines = []
    cat_cols  = df.select_dtypes(include=["object", "category"]).columns
    for col in list(cat_cols)[:5]:
        uniq = df[col].dropna().unique()
        sample = ", ".join(str(v) for v in uniq[:5])
        if len(uniq) > 5:
            sample += f" …（共 {len(uniq)} 種）"
        cat_lines.append(f"  • {col}: {sample}")

    # ── 前 5 筆預覽（最多 10 欄，防止太寬）──────────────────────────────────
    preview_df = df.head(5).iloc[:, :10]
    preview    = preview_df.to_string(index=False)

    # ── 組合摘要 ──────────────────────────────────────────────────────────────
    parts = [
        f"【檔案】{filename}",
        f"【規模】{rows:,} 筆資料，{cols} 個欄位",
        "",
        "【欄位清單】",
        *col_lines,
    ]

    if stats_lines:
        parts += ["", "【數值統計】", *stats_lines]

    if cat_lines:
        parts += ["", "【文字欄位樣本】", *cat_lines]

    parts += ["", "【前 5 筆預覽】", preview]

    summary = "\n".join(parts)
    return summary, rows, cols


def _read_csv_auto_encoding(file_bytes: bytes):
    """自動嘗試 UTF-8 → UTF-8-BOM → Big5 編碼讀取 CSV。"""
    import pandas as pd

    for enc in ("utf-8-sig", "utf-8", "big5", "gbk"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
        except (UnicodeDecodeError, Exception):
            continue
    # 最後嘗試 latin-1（不會拋出 decode error）
    return pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
