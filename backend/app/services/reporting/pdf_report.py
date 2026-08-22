"""Master PDF Document Builder & Numbered Canvas for Sentinel AI.
Compiles professional multi-page fraud intelligence reports with running headers,
dynamic page numbering (Page X of Y), and strict styling.
"""
import io
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, PageBreak, Spacer
from reportlab.pdfgen import canvas

from ...core.session_store import AnalysisSession
from .sections import ReportSectionsBuilder


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas calculating total page count dynamically.
    Draws professional running headers and footers on every page.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 756, "SENTINEL AI — Risk Intelligence & Fraud Analysis Audit")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)

        # Running Footer (All Pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 38, 576, 38)

        # Footer Left: Confidentiality Note
        self.drawString(36, 26, "Sentinel AI • Internal Risk Intelligence Report • Confidential Audit")

        # Footer Right: Page X of Y
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 26, page_str)

        self.restoreState()


class PDFReportGenerator:
    """Orchestrates PDF report construction from an active AnalysisSession."""

    @classmethod
    def generate_report(cls, session: AnalysisSession) -> bytes:
        """Assembles all sections, executes ReportLab layout engine, and returns PDF bytes."""
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=46,
            bottomMargin=46
        )

        builder = ReportSectionsBuilder(session)
        story = []

        # Cover & Executive Summary
        story.extend(builder.build_cover_section())
        story.extend(builder.build_executive_summary_section())
        story.extend(builder.build_dataset_quality_section())

        story.append(PageBreak())

        # Risk & Analytics Deep Dive
        story.extend(builder.build_risk_overview_section())
        story.extend(builder.build_fraud_analytics_section())

        story.append(PageBreak())

        # Machine Learning Benchmarking & Risk Factors
        story.extend(builder.build_model_performance_section())
        story.extend(builder.build_risk_factors_section())

        story.append(PageBreak())

        # Sample High-Risk Transactions & Recommendations
        story.extend(builder.build_high_risk_transactions_section())
        story.extend(builder.build_findings_and_recommendations_section())

        story.append(PageBreak())

        # Methodology & Limitations
        story.extend(builder.build_methodology_and_limitations_section())

        # Build PDF with two-pass NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
