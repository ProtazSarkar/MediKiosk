import os
import html
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def format_text_for_reportlab(text):
    """
    Sanitizes raw text and formats basic markdown (bold, line breaks) into ReportLab-compatible XML.
    """
    if not text:
        return ""

    # Escape XML/HTML special characters first (<, >, &)
    text = html.escape(text)

    # Convert markdown bold **text** to <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Convert markdown italic *text* to <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)

    # Replace newlines with <br/> for ReportLab paragraph rendering
    text = text.replace('\n', '<br/>')

    return text

def generate_pdf_summary(user_id, history):
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

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")    # Dark Slate
    ACCENT = colors.HexColor("#0284C7")     # Medical Blue
    PATIENT_COLOR = colors.HexColor("#0369A1")  # Deep Blue
    AI_COLOR = colors.HexColor("#0D9488")       # Teal
    BG_LIGHT = colors.HexColor("#F8FAFC")     # Soft Gray background
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
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
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=12
    )

    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#78350F"),
    )

    header_msg_style_user = ParagraphStyle(
        'MsgHeaderUser',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=PATIENT_COLOR,
        spaceAfter=2
    )

    header_msg_style_ai = ParagraphStyle(
        'MsgHeaderAI',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=AI_COLOR,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'MsgBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
    )

    # 1. Document Title & Subtitle Header
    story.append(Paragraph("MediKiosk - Medical Consultation Summary", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=10))

    # 2. Consultation Metadata Table
    meta_data = [
        [
            Paragraph("<b>Consultation ID:</b>", body_style),
            Paragraph(f"<code>{user_id}</code>", body_style),
            Paragraph("<b>Total Messages:</b>", body_style),
            Paragraph(str(len(history)), body_style)
        ],
        [
            Paragraph("<b>Status:</b>", body_style),
            Paragraph("<font color='#059669'>Completed (Summary Ready)</font>", body_style),
            Paragraph("<b>Format:</b>", body_style),
            Paragraph("Preliminary AI Triage Summary", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[110, 160, 100, 170])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # 3. Legal/Medical Disclaimer Box
    disclaimer_p = Paragraph(
        "<b>NOTICE:</b> This document contains a summary of an automated preliminary consultation log. "
        "It does NOT constitute a formal medical diagnosis or treatment plan. "
        "Please present this summary to a licensed physician or healthcare professional for clinical evaluation.",
        disclaimer_style
    )
    disc_table = Table([[disclaimer_p]], colWidths=[540])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")), # Light Amber
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#F59E0B")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(disc_table)
    story.append(Spacer(1, 14))

    # 4. Consultation Conversation Log Section Header
    story.append(Paragraph("<b>Consultation Transcript</b>", ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=PRIMARY,
        spaceAfter=8
    )))

    # 5. Message Cards
    for idx, message in enumerate(history, 1):
        is_user = (message["role"] == "user")
        role_label = f"Patient (Entry #{idx})" if is_user else f"MediKiosk Assistant (Entry #{idx})"
        header_st = header_msg_style_user if is_user else header_msg_style_ai
        bg_card = colors.HexColor("#F0F9FF") if is_user else colors.HexColor("#F0FDF4")
        border_card = colors.HexColor("#BAE6FD") if is_user else colors.HexColor("#BBF7D0")

        formatted_content = format_text_for_reportlab(message.get("content", ""))

        card_content = [
            Paragraph(role_label, header_st),
            Spacer(1, 2),
            Paragraph(formatted_content, body_style)
        ]

        card_table = Table([[card_content]], colWidths=[540])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_card),
            ('BOX', (0, 0), (-1, -1), 0.5, border_card),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(KeepTogether([card_table, Spacer(1, 8)]))

    doc.build(story)
    return pdf_path