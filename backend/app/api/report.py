# -*- coding: utf-8 -*-
"""
报告导出 API。

支持 PDF 与 Excel 两种格式导出单样本检测报告。
"""

import io
from datetime import datetime

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.dao.detection_dao import DetectionResultDAO
from app.dao.library_dao import DrugDAO
from app.dao.sample_dao import SampleDAO
from app.errors.exceptions import NotFoundException, ParamValidationException
from app.service.log_service import log_operation
from app.utils.pdf_fonts import register_chinese_font
from app.utils.report_chart import generate_chromatogram_chart
from app.utils.timezone import format_cn_time, now_cn

# 模块加载时注册中文字体，供后续 PDF 生成使用
_CHINESE_FONT = register_chinese_font()

report_bp = Blueprint("report", __name__)


@report_bp.route("/reports/<int:sample_id>/download", methods=["GET"])
@jwt_required()
def download_report_view(sample_id: int):
    """
    下载样本检测报告。

    查询参数：format=pdf|excel，默认 pdf
    """
    fmt = (request.args.get("format", "pdf") or "pdf").lower()
    if fmt not in ("pdf", "excel"):
        raise ParamValidationException("format 仅支持 pdf 或 excel")

    sample = SampleDAO.get_by_id(sample_id)
    if sample is None:
        raise NotFoundException("样本不存在")

    results = DetectionResultDAO.get_by_sample_id(sample_id)
    detected = [r for r in results if r.is_detected]

    if fmt == "pdf":
        buffer = _build_pdf(sample, detected, results)
        mimetype = "application/pdf"
        ext = "pdf"
    else:
        buffer = _build_excel(sample, detected, results)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"

    filename = f"report_{sample.sample_no}_{now_cn().strftime('%Y%m%d%H%M%S')}.{ext}"
    buffer.seek(0)

    log_operation(
        action=f"下载{fmt.upper()}报告",
        module="report",
        target_type="sample",
        target_id=sample_id,
        detail={"format": fmt, "filename": filename},
    )

    return send_file(
        buffer,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename,
    )


def _build_pdf(sample, detected, all_results):
    """生成 PDF 报告（正式报告格式，含色谱对照图）。"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()

    # 中文字体样式
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName=_CHINESE_FONT,
        fontSize=20,
        alignment=1,
        spaceAfter=14,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontName=_CHINESE_FONT,
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1a2980"),
    )
    normal_style = ParagraphStyle(
        "ReportNormal",
        parent=styles["Normal"],
        fontName=_CHINESE_FONT,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#333333"),
    )
    label_style = ParagraphStyle(
        "ReportLabel",
        parent=styles["Normal"],
        fontName=_CHINESE_FONT,
        fontSize=10,
        leading=16,
        textColor=colors.HexColor("#555555"),
    )
    footer_style = ParagraphStyle(
        "ReportFooter",
        parent=styles["Normal"],
        fontName=_CHINESE_FONT,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#666666"),
    )

    story = []

    # 报告标题
    story.append(Paragraph("HPLC-DAD 非法添加药物筛查检测报告", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a2980"), spaceAfter=12))

    # 基本信息
    detect_time = sample.detect_time or sample.created_at
    info_data = [
        ["样品编号", sample.sample_no, "样品名称", sample.sample_name or "-"],
        ["检测时间", format_cn_time(detect_time), "仪器品牌", sample.instrument_brand or "-"],
        ["候选药物数", str(len(all_results)), "检出药物数", str(len(detected))],
    ]
    info_table = Table(info_data, colWidths=[25 * mm, 55 * mm, 25 * mm, 55 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef2f7")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
        ("FONTNAME", (0, 0), (-1, -1), _CHINESE_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # 检测结果汇总
    story.append(Paragraph("一、检测结果汇总", heading_style))
    if detected:
        # 按置信度降序
        detected_sorted = sorted(detected, key=lambda r: r.confidence or 0, reverse=True)
        data = [["序号", "药物名称", "综合评分", "置信度", "匹配峰数", "判定"]]
        for idx, r in enumerate(detected_sorted, 1):
            drug = DrugDAO.get_by_id(r.drug_id)
            data.append([
                str(idx),
                drug.name if drug else str(r.drug_id),
                f"{r.total_score:.4f}" if r.total_score else "-",
                f"{r.confidence:.4f}" if r.confidence else "-",
                f"{r.matched_peak_count}/{r.total_peak_count}",
                "检出",
            ])
        table = Table(data, colWidths=[18 * mm, 50 * mm, 26 * mm, 26 * mm, 26 * mm, 20 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2980")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7de")),
            ("FONTNAME", (0, 0), (-1, -1), _CHINESE_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("未检出目标药物。", normal_style))

    # 色谱对照图
    chart_drug_id = None
    if detected:
        chart_drug_id = max(detected, key=lambda r: r.confidence or 0).drug_id
    chart_bytes = generate_chromatogram_chart(sample, drug_id=chart_drug_id)
    if chart_bytes:
        story.append(Spacer(1, 16))
        story.append(Paragraph("二、色谱峰形对比图", heading_style))
        story.append(Paragraph("蓝色曲线为样本色谱，橙色曲线/标记为对应标准品参考峰。", label_style))
        story.append(Spacer(1, 6))
        img = Image(io.BytesIO(chart_bytes), width=170 * mm, height=76.5 * mm)
        story.append(img)

    # 备注与签章
    story.append(Spacer(1, 20))
    story.append(Paragraph("三、检测说明", heading_style))
    story.append(Paragraph(
        "本报告基于 HPLC-DAD 色谱保留时间、峰面积比及紫外光谱相似度等多维特征，"
        "采用融合模型与贝叶斯判别算法生成。结果仅供实验室内部筛查参考，"
        "最终判定请结合标准方法及人工复核。",
        normal_style,
    ))
    story.append(Spacer(1, 30))
    story.append(Paragraph("检测人：_______________    复核人：_______________    日期：_______________", footer_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("实验室管理系统自动生成，禁止私自涂改。", footer_style))

    doc.build(story)
    return buffer


def _build_excel(sample, detected, all_results):
    """生成 Excel 报告。"""
    buffer = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "检测报告"

    ws.append(["HPLC-DAD 药物检测报告"])
    ws.append(["样品编号", sample.sample_no])
    ws.append(["样品名称", sample.sample_name or "-"])
    detect_time = sample.detect_time or sample.created_at
    ws.append(["检测时间", format_cn_time(detect_time)])
    ws.append(["候选药物数", len(all_results)])
    ws.append(["检出药物数", len(detected)])
    ws.append([])

    ws.append(["药物名称", "综合评分", "置信度", "匹配峰数", "是否检出"])
    for r in all_results:
        drug = DrugDAO.get_by_id(r.drug_id)
        ws.append([
            drug.name if drug else r.drug_id,
            r.total_score,
            r.confidence,
            f"{r.matched_peak_count}/{r.total_peak_count}",
            "是" if r.is_detected else "否",
        ])

    wb.save(buffer)
    return buffer
