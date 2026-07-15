# -*- coding: utf-8 -*-
"""
检测报告图表生成辅助模块。

使用 matplotlib 绘制 HPLC 样本色谱与标准品对照峰叠加图，供 PDF 报告嵌入。
"""

import io
import os
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from app.dao.file_dao import UploadedFileDAO
from app.dao.library_dao import ReferencePeakDAO
from app.model import Sample
from app.service.file_service import parse_file_to_chromatogram


# 中文字体候选，与 pdf_fonts 保持一致（Windows + Linux）
_FONT_CANDIDATES = [
    ("C:/Windows/Fonts/simhei.ttf", None),
    ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/simsun.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
]


def _get_font_properties():
    """尝试找到可用的中文字体。"""
    for path, idx in _FONT_CANDIDATES:
        if not os.path.isfile(path):
            continue
        try:
            return FontProperties(fname=path)
        except Exception:
            continue
    return None


_CHINESE_FONT = _get_font_properties()


def _build_reference_curve(
    time,
    ref_peaks: List[Any],
    scale_max: float,
):
    """根据参考峰生成一条合成标准品曲线（高斯叠加）。"""
    total_ratio = float(sum((p.area_ratio or 0.2) for p in ref_peaks)) or len(ref_peaks)
    intensity = []
    for t in time:
        y = 0.0
        for p in ref_peaks:
            rt = float(p.retention_time)
            width = float(p.width) if p.width else 0.08
            sigma = width / 2.355 if width > 0 else 0.05
            ratio = float(p.area_ratio) if p.area_ratio else 0.2
            amp = (ratio / total_ratio) * scale_max * 0.95
            y += amp * 2.718281828 ** (-0.5 * ((t - rt) / sigma) ** 2)
        intensity.append(y)
    return intensity


def generate_chromatogram_chart(
    sample: Sample,
    drug_id: Optional[int] = None,
    figsize=(8, 3.6),
    dpi: int = 150,
) -> Optional[bytes]:
    """
    生成色谱对比图 PNG 字节。

    :param sample: 样本对象
    :param drug_id: 用于对照的标准药物 ID，为空则只绘制样本
    :return: PNG 图像字节；失败返回 None
    """
    if sample.file_id is None:
        return None

    file_record = UploadedFileDAO.get_by_id(sample.file_id)
    if file_record is None:
        return None

    try:
        chromatogram = parse_file_to_chromatogram(file_record)
    except Exception:
        return None

    time = chromatogram.retention_time
    intensity = chromatogram.intensity
    sample_peaks = sample.peaks

    ref_peaks = []
    if drug_id:
        ref_peaks = ReferencePeakDAO.get_by_drug_id(drug_id)

    # 亮色主题配色，便于嵌入白色 PDF 页面
    bg_color = '#ffffff'
    text_color = '#1f2937'
    grid_color = '#d1d5db'
    spine_color = '#9ca3af'
    sample_line = '#2563eb'
    sample_fill = '#2563eb'
    sample_peak = '#16a34a'
    ref_line = '#d97706'
    ref_fill = '#d97706'
    ref_text = '#92400e'

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    # 样本色谱曲线
    ax.plot(
        time,
        intensity,
        color=sample_line,
        linewidth=1.8,
        label='样本色谱',
        alpha=0.95,
    )
    ax.fill_between(time, intensity, color=sample_fill, alpha=0.12)

    # 样本峰标记
    if sample_peaks:
        sample_peak_rts = [float(p.retention_time) for p in sample_peaks]
        sample_peak_vals = []
        for rt in sample_peak_rts:
            idx = int(abs(time - rt).argmin())
            sample_peak_vals.append(intensity[idx])
        ax.scatter(
            sample_peak_rts,
            sample_peak_vals,
            color=sample_peak,
            s=55,
            zorder=5,
            edgecolors='white',
            linewidths=0.8,
            label='样本峰',
        )

    # 标准品曲线与参考峰
    if ref_peaks:
        sample_max = float(intensity.max()) if len(intensity) else 1.0
        ref_curve = _build_reference_curve(time, ref_peaks, sample_max)
        ax.plot(
            time,
            ref_curve,
            color=ref_line,
            linewidth=1.6,
            label='标准品曲线',
            alpha=0.92,
        )
        ax.fill_between(time, ref_curve, color=ref_fill, alpha=0.10)

        for p in ref_peaks:
            rt = float(p.retention_time)
            idx = int(abs(time - rt).argmin())
            val = ref_curve[idx]
            ax.axvline(
                rt,
                color=ref_line,
                linestyle='--',
                linewidth=0.8,
                alpha=0.45,
            )
            ax.scatter(
                [rt],
                [val],
                color=ref_line,
                s=70,
                zorder=5,
                edgecolors='white',
                linewidths=1,
            )
            ax.text(
                rt,
                val * 1.08,
                f"P{int(p.peak_index)}",
                color=ref_text,
                fontsize=7,
                ha='center',
                fontproperties=_CHINESE_FONT,
            )

    ax.set_xlabel('保留时间 (min)', color=text_color, fontproperties=_CHINESE_FONT, fontsize=10)
    ax.set_ylabel('响应值', color=text_color, fontproperties=_CHINESE_FONT, fontsize=10)
    ax.tick_params(axis='both', colors=text_color, labelsize=8)
    ax.spines['bottom'].set_color(spine_color)
    ax.spines['left'].set_color(spine_color)
    ax.spines['top'].set_color(grid_color)
    ax.spines['right'].set_color(grid_color)
    ax.grid(True, linestyle='--', alpha=0.5, color=grid_color)

    title = f"样本 {sample.sample_no} 色谱图"
    if ref_peaks:
        title += " 与标准品对照"
    ax.set_title(title, color=text_color, fontsize=12, fontproperties=_CHINESE_FONT, pad=10)

    legend = ax.legend(
        loc='upper right',
        framealpha=0.9,
        facecolor=bg_color,
        edgecolor=spine_color,
        fontsize=8,
    )
    if legend is not None:
        for text in legend.get_texts():
            text.set_color(text_color)
            text.set_fontproperties(_CHINESE_FONT)

    plt.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight', facecolor=bg_color)
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()
