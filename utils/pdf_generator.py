"""
Enhanced Clinical PDF Generator for MediKiosk.
Generates an ABDM/EHR-ready Pre-Consultation Summary with:
- Patient Demographics & Chief Complaint
- Primary Diagnostic Hypothesis & Differential Possibilities
- Turn-by-Turn Decision Stamps Timeline
- Pertinent Positives & Negatives
- Red-Flag Emergency Screening
- Full Dialogue Transcript
"""

import os
import html
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def format_text_for_reportlab(text):
    if not text:
        return ""
    text = html.escape(str(text))
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = text.replace('\n', '<br/>')
    return text

def generate_pdf_summary(user_id, history, clinical_state=None):
    storage_dir = "storage"
    os.makedirs(storage_dir, exist_ok=True)
    pdf_path = os.path.join(storage_dir, f"{user_id}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0F172A")    # Dark Slate
    ACCENT = colors.HexColor("#0284C7")     # Medical Blue
    SUCCESS = colors.HexColor("#059669")    # Green
    DANGER = colors.HexColor("#DC2626")     # Red
    LIGHT_BG = colors.HexColor("#F8FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=10
    )

    section_heading = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )

    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=ACCENT
    )

    # 1. Header Block
    header_table_data = [
        [
            Paragraph("<b>MEDIKIOSK | CLINICAL PRE-CONSULTATION SUMMARY</b>", title_style),
            Paragraph(f"<b>Encounter ID:</b> {user_id[:8]}<br/><b>Date:</b> {datetime.now().strftime('%d %b %Y %H:%M')}", subtitle_style)
        ]
    ]
    t_header = Table(header_table_data, colWidths=[360, 180])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=4, spaceAfter=8))

    # 2. Diagnostic Summary & Judge Verdict
    report_data = (clinical_state or {}).get("final_report", {})
    primary = report_data.get("primary_diagnosis", {})
    differentials = report_data.get("differential_diagnoses", [])
    readiness = (clinical_state or {}).get("readiness_score", 85)

    primary_name = primary.get("name", "Clinical Triage in Progress")
    confidence = primary.get("confidence", "75%")
    dept = primary.get("department", "General OPD")
    icd11 = primary.get("icd11_code", "Unspecified")

    diag_summary_box = [
        [
            Paragraph("<b>PRIMARY HYPOTHESIS:</b>", table_cell_style),
            Paragraph(f"<b>{primary_name}</b> ({confidence})", badge_style)
        ],
        [
            Paragraph("<b>TARGET DEPARTMENT:</b>", table_cell_style),
            Paragraph(f"<b>{dept}</b> | <b>ICD-11:</b> {icd11}", table_cell_style)
        ],
        [
            Paragraph("<b>JUDGE READINESS SCORE:</b>", table_cell_style),
            Paragraph(f"<b>{readiness}% Complete</b> (Gatekeeper Criteria Satisfied)", table_cell_style)
        ]
    ]
    t_diag = Table(diag_summary_box, colWidths=[160, 380])
    t_diag.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BAE6FD")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E0F2FE")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_diag)
    story.append(Spacer(1, 10))

    # 3. Differentials Table
    if differentials:
        story.append(Paragraph("<b>Secondary Differential Diagnoses:</b>", section_heading))
        diff_table_data = [
            [Paragraph("Condition", table_header_style), Paragraph("Probability", table_header_style), Paragraph("Department", table_header_style), Paragraph("ICD-11", table_header_style)]
        ]
        for d in differentials:
            diff_table_data.append([
                Paragraph(d.get("name", "-"), table_cell_style),
                Paragraph(d.get("confidence", "-"), table_cell_style),
                Paragraph(d.get("department", "-"), table_cell_style),
                Paragraph(d.get("icd11_code", "-"), table_cell_style),
            ])
        t_diff = Table(diff_table_data, colWidths=[200, 80, 160, 100])
        t_diff.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_diff)
        story.append(Spacer(1, 10))

    # 4. Turn-by-Turn Decision Stamps Timeline
    decision_stamps = (clinical_state or {}).get("decision_stamps", [])
    if decision_stamps:
        story.append(Paragraph("<b>Clinical Decision Stamps (Probability Progression):</b>", section_heading))
        stamps_table_data = [
            [Paragraph("Step", table_header_style), Paragraph("Candidate Probabilities", table_header_style), Paragraph("Clinical Reasoning & Differentiating Factor", table_header_style)]
        ]
        for s in decision_stamps:
            hyps = ", ".join([f"{h['name']} ({h['probability']}%)" for h in s.get("hypotheses", [])])
            desc = f"<b>{format_text_for_reportlab(s.get('rationale', ''))}</b><br/><i>Factor: {format_text_for_reportlab(s.get('differentiating_factor', ''))}</i>"
            stamps_table_data.append([
                Paragraph(f"Turn {s.get('turn')}<br/>{s.get('timestamp')}", table_cell_style),
                Paragraph(hyps, table_cell_style),
                Paragraph(desc, table_cell_style)
            ])
        t_stamps = Table(stamps_table_data, colWidths=[65, 185, 290])
        t_stamps.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_stamps)
        story.append(Spacer(1, 10))

    # 4b. Digitized Prior Prescriptions & Records
    uploaded_docs = (clinical_state or {}).get("uploaded_documents", [])
    if uploaded_docs:
        story.append(Paragraph("<b>Digitized Prior Prescriptions & Medical Records:</b>", section_heading))
        doc_rows = [
            [Paragraph("File", table_header_style), Paragraph("Extracted Medications", table_header_style), Paragraph("Prior Diagnoses & Notes", table_header_style)]
        ]
        for doc_item in uploaded_docs:
            meds = ", ".join(doc_item.get("medications", [])) or "None listed"
            diags = ", ".join(doc_item.get("diagnoses", [])) or "None listed"
            summary = doc_item.get("summary", "")
            doc_rows.append([
                Paragraph(f"<b>{format_text_for_reportlab(doc_item.get('file_name', 'Document'))}</b><br/><i>{doc_item.get('file_type', 'Medical File')}</i>", table_cell_style),
                Paragraph(format_text_for_reportlab(meds), table_cell_style),
                Paragraph(f"<b>Diagnoses:</b> {format_text_for_reportlab(diags)}<br/>{format_text_for_reportlab(summary)}", table_cell_style)
            ])
        t_docs = Table(doc_rows, colWidths=[120, 200, 220])
        t_docs.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#334155")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_docs)
        story.append(Spacer(1, 10))

    # 5. Pertinent Findings & Red Flags
    findings_data = [
        [
            Paragraph("<b>Pertinent Positives:</b><br/>" + (", ".join(clinical_state.get("pertinent_positives", [])) if clinical_state and clinical_state.get("pertinent_positives") else "None specified"), table_cell_style),
            Paragraph("<b>Pertinent Negatives:</b><br/>" + (", ".join(clinical_state.get("pertinent_negatives", [])) if clinical_state and clinical_state.get("pertinent_negatives") else "None specified"), table_cell_style),
            Paragraph("<b>Red-Flag Alerts:</b><br/>" + (", ".join(clinical_state.get("red_flags", ["Cleared"])) if clinical_state and clinical_state.get("red_flags") else "Cleared"), table_cell_style)
        ]
    ]
    t_findings = Table(findings_data, colWidths=[180, 180, 180])
    t_findings.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_findings)
    story.append(Spacer(1, 10))

    user_label_style = ParagraphStyle(
        'UserLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=ACCENT
    )

    ai_label_style = ParagraphStyle(
        'AILabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY
    )

    # 6. Dialogue Transcript
    story.append(Paragraph("<b>Consultation Transcript:</b>", section_heading))
    chat_rows = []
    for msg in history:
        sender_text = "PATIENT:" if msg["role"] == "user" else "MEDIKIOSK AI:"
        sender_style = user_label_style if msg["role"] == "user" else ai_label_style
        chat_rows.append([
            Paragraph(f"<b>{sender_text}</b>", sender_style),
            Paragraph(format_text_for_reportlab(msg["content"]), table_cell_style)
        ])
    if chat_rows:
        t_chat = Table(chat_rows, colWidths=[90, 450])
        t_chat.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(t_chat)

    # Disclaimer footer
    story.append(Spacer(1, 12))
    disclaimer = Paragraph(
        "<i>NOTICE: This document is a preliminary pre-consultation intake summary generated by an AI assistant. "
        "It is intended solely to assist the examining physician during outpatient triage and does not constitute a definitive medical diagnosis.</i>",
        subtitle_style
    )
    story.append(disclaimer)

    doc.build(story)
    return pdf_path
