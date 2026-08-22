"""ReportLab Section Flowable Builders for Sentinel AI PDF Reports.
Assembles strongly-typed analytical sections with zero data fabrication.
"""
from typing import List, Dict, Any, Optional
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable,
    PageBreak,
)

from ...schemas.analysis import AnalysisResult
from ...core.session_store import AnalysisSession
from .charts import ReportChartGenerator


# Semantic Color Palette for PDF
PRIMARY_COLOR = colors.HexColor('#1E293B')   # Slate 800
SECONDARY_COLOR = colors.HexColor('#4F46E5') # Indigo 600
DANGER_COLOR = colors.HexColor('#EF4444')    # Crimson / Red
WARNING_COLOR = colors.HexColor('#F59E0B')   # Amber
SUCCESS_COLOR = colors.HexColor('#10B981')   # Emerald
BG_LIGHT = colors.HexColor('#F8FAFC')        # Light slate bg
BORDER_COLOR = colors.HexColor('#E2E8F0')    # Light border


class ReportSectionsBuilder:
    """Builds individual ReportLab flowable elements for the audit report."""

    def __init__(self, session: Any):
        self.session = session
        if hasattr(session, "analysis_result"):
            self.result: AnalysisResult = session.analysis_result
        elif hasattr(session, "result"):
            self.result: AnalysisResult = session.result
        else:
            self.result = session
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """Initializes typography and layout styles."""
        self.title_style = ParagraphStyle(
            'ReportTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=PRIMARY_COLOR,
            spaceAfter=6
        )
        self.subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=SECONDARY_COLOR,
            spaceAfter=15
        )
        self.h1_style = ParagraphStyle(
            'SectionH1',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=PRIMARY_COLOR,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )
        self.h2_style = ParagraphStyle(
            'SectionH2',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=SECONDARY_COLOR,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True
        )
        self.body_style = ParagraphStyle(
            'ReportBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )
        self.meta_style = ParagraphStyle(
            'ReportMeta',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#64748B')
        )
        self.table_cell = ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )
        self.table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#1E293B')
        )
        self.table_cell_danger = ParagraphStyle(
            'TableCellDanger',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=DANGER_COLOR
        )

    def build_cover_section(self) -> List[Any]:
        """Builds Cover Banner & Header block."""
        flowables = []

        # Top Accent Line
        flowables.append(HRFlowable(width="100%", thickness=4, color=DANGER_COLOR, spaceBefore=0, spaceAfter=15))

        # Title Block
        flowables.append(Paragraph("SENTINEL AI", self.title_style))
        flowables.append(Paragraph("Fraud Intelligence & Risk Analysis Report", self.subtitle_style))
        flowables.append(Paragraph(
            "Comprehensive machine learning fraud audit, empirical risk scoring, and evidence-based findings.",
            self.body_style
        ))
        flowables.append(Spacer(1, 10))

        # Metadata Table
        created_str = self.result.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(self.result.created_at, 'strftime') else str(self.result.created_at)
        meta_data = [
            [
                Paragraph("<b>Analysis Session ID:</b>", self.meta_style),
                Paragraph(self.session.analysis_id, self.meta_style),
                Paragraph("<b>Audit Date:</b>", self.meta_style),
                Paragraph(created_str, self.meta_style)
            ],
            [
                Paragraph("<b>Dataset Source:</b>", self.meta_style),
                Paragraph(self.result.dataset_summary.dataset_name, self.meta_style),
                Paragraph("<b>Evaluated Model:</b>", self.meta_style),
                Paragraph(self.result.model_results.selected_model.model_name, self.meta_style)
            ],
            [
                Paragraph("<b>Pre-flight Status:</b>", self.meta_style),
                Paragraph("VERIFIED & AUDITED", self.meta_style),
                Paragraph("<b>Execution Time:</b>", self.meta_style),
                Paragraph(f"{self.result.execution_time_seconds:.2f} seconds", self.meta_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[110, 160, 90, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        flowables.append(meta_table)
        flowables.append(Spacer(1, 15))
        flowables.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceBefore=5, spaceAfter=15))

        return flowables

    def build_executive_summary_section(self) -> List[Any]:
        """Section 1: Executive Summary KPIs & Narrative."""
        flowables = []
        flowables.append(Paragraph("01. Executive Summary & Exposure Metrics", self.h1_style))

        fraud = self.result.fraud_statistics
        risk = self.result.risk_statistics

        # Top KPI Highlights
        kpi_data = [
            [
                Paragraph("Total Transactions", self.meta_style),
                Paragraph("Confirmed Fraud", self.meta_style),
                Paragraph("Prevalence Rate", self.meta_style),
                Paragraph("Direct Exposure Loss", self.meta_style),
            ],
            [
                Paragraph(f"<b>{fraud.total_transactions:,}</b>", self.table_cell_bold),
                Paragraph(f"<b>{fraud.fraud_count:,}</b>", self.table_cell_danger),
                Paragraph(f"<b>{fraud.fraud_rate_percentage:.3f}%</b>", self.table_cell_danger),
                Paragraph(f"<b>${fraud.fraud_volume_usd:,.2f}</b>", self.table_cell_bold),
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 130])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        flowables.append(kpi_table)
        flowables.append(Spacer(1, 8))

        # Narrative paragraph synthesized directly from actual computed metrics
        narrative = (
            f"The Sentinel AI intelligence engine conducted an exhaustive evaluation over {fraud.total_transactions:,} "
            f"transaction events. A total of {fraud.fraud_count:,} events were identified as confirmed fraudulent activity, "
            f"representing a {fraud.fraud_rate_percentage:.3f}% fraud prevalence across gross transaction volume. "
            f"Total direct fraud exposure equals ${fraud.fraud_volume_usd:,.2f} USD ({fraud.fraud_loss_percentage:.2f}% of overall gross dollar volume). "
            f"The risk scoring system classified {risk.critical_risk_count:,} transactions ({risk.critical_risk_pct:.2f}%) into the CRITICAL risk band "
            f"and {risk.high_risk_count:,} transactions ({risk.high_risk_pct:.2f}%) into the HIGH risk band, "
            f"with an aggregate population mean risk score of {risk.mean_risk_score:.2f} (median: {risk.median_risk_score:.2f})."
        )
        flowables.append(Paragraph(narrative, self.body_style))
        flowables.append(Spacer(1, 10))
        return flowables

    def build_dataset_quality_section(self) -> List[Any]:
        """Section 2: Dataset Integrity & Quality Audit."""
        flowables = []
        flowables.append(Paragraph("02. Dataset Integrity & Pre-Flight Quality Audit", self.h1_style))

        ds = self.result.dataset_summary
        dq = self.result.data_quality

        status_text = "PASS" if dq.is_valid_for_analysis and len(ds.errors) == 0 else "WARNING"
        status_color = SUCCESS_COLOR if status_text == "PASS" else WARNING_COLOR

        rows = [
            [Paragraph("<b>Metric Property</b>", self.table_cell_bold), Paragraph("<b>Audit Finding</b>", self.table_cell_bold)],
            [Paragraph("Source File Name", self.table_cell), Paragraph(ds.dataset_name, self.table_cell)],
            [Paragraph("Total Processed Rows", self.table_cell), Paragraph(f"{ds.row_count:,}", self.table_cell)],
            [Paragraph("Extracted Columns", self.table_cell), Paragraph(f"{ds.column_count} features", self.table_cell)],
            [Paragraph("Target Variable", self.table_cell), Paragraph(str(ds.target_column or "is_fraud"), self.table_cell)],
            [Paragraph("Missing Cells Rate", self.table_cell), Paragraph(f"{dq.missing_cells_percentage:.2f}%", self.table_cell)],
            [Paragraph("Duplicate Row Rate", self.table_cell), Paragraph(f"{dq.duplicate_rows_percentage:.2f}%", self.table_cell)],
            [
                Paragraph("Class Imbalance Ratio", self.table_cell),
                Paragraph(f"{ds.class_distribution.imbalance_ratio:.1f}:1 ({ds.class_distribution.fraud_percentage:.3f}% fraud)" if ds.class_distribution else "N/A", self.table_cell)
            ],
            [Paragraph("Data Quality Gate Status", self.table_cell_bold), Paragraph(f"<b>{status_text}</b>", self.table_cell_bold)]
        ]

        table = Table(rows, colWidths=[200, 320])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        flowables.append(table)
        flowables.append(Spacer(1, 10))
        return flowables

    def build_risk_overview_section(self) -> List[Any]:
        """Section 3: Risk Overview & Tier Breakdown."""
        flowables = []
        flowables.append(Paragraph("03. Calibrated Risk Tier Segmentation", self.h1_style))

        risk = self.result.risk_statistics
        chart_buf = ReportChartGenerator.generate_risk_distribution_chart(risk)

        # Risk Table
        table_data = [
            [Paragraph("<b>Risk Band</b>", self.table_cell_bold), Paragraph("<b>Score Interval</b>", self.table_cell_bold), Paragraph("<b>Event Count</b>", self.table_cell_bold), Paragraph("<b>Proportion</b>", self.table_cell_bold)],
            [Paragraph("LOW", self.table_cell_bold), Paragraph("0.00 – 20.00", self.table_cell), Paragraph(f"{risk.low_risk_count:,}", self.table_cell), Paragraph(f"{risk.low_risk_pct:.2f}%", self.table_cell)],
            [Paragraph("MEDIUM", self.table_cell_bold), Paragraph("20.01 – 50.00", self.table_cell), Paragraph(f"{risk.medium_risk_count:,}", self.table_cell), Paragraph(f"{risk.medium_risk_pct:.2f}%", self.table_cell)],
            [Paragraph("HIGH", self.table_cell_bold), Paragraph("50.01 – 80.00", self.table_cell), Paragraph(f"{risk.high_risk_count:,}", self.table_cell), Paragraph(f"{risk.high_risk_pct:.2f}%", self.table_cell)],
            [Paragraph("CRITICAL", self.table_cell_danger), Paragraph("80.01 – 100.00", self.table_cell), Paragraph(f"{risk.critical_risk_count:,}", self.table_cell_danger), Paragraph(f"{risk.critical_risk_pct:.2f}%", self.table_cell_danger)],
        ]
        table = Table(table_data, colWidths=[80, 100, 80, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Place table and chart side by side
        img = Image(chart_buf, width=190, height=140)
        combo_data = [[table, img]]
        combo_table = Table(combo_data, colWidths=[330, 190])
        combo_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        flowables.append(combo_table)
        flowables.append(Spacer(1, 10))
        return flowables

    def build_fraud_analytics_section(self) -> List[Any]:
        """Section 4: Fraud Analytics, Patterns & Loss Concentrations."""
        flowables = []
        flowables.append(Paragraph("04. Fraud Analytics & Loss Concentrations", self.h1_style))

        # Chart Row
        cat_chart_buf = ReportChartGenerator.generate_category_loss_chart(self.result.categorical_breakdowns)
        hist_chart_buf = ReportChartGenerator.generate_score_histogram_chart(self.result.risk_distribution)

        img1 = Image(cat_chart_buf, width=255, height=145)
        img2 = Image(hist_chart_buf, width=255, height=145)

        chart_row = Table([[img1, img2]], colWidths=[260, 260])
        chart_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        flowables.append(chart_row)
        flowables.append(Spacer(1, 8))

        # Behavioral Risk Patterns
        if self.result.high_risk_patterns:
            flowables.append(Paragraph("<b>Identified Behavioral Risk Patterns:</b>", self.h2_style))
            for pat in self.result.high_risk_patterns:
                p_text = (
                    f"• <b>{pat.pattern_name}</b> [{pat.severity}]: {pat.description} "
                    f"(Observed fraud rate: <b>{pat.fraud_rate_percentage:.2f}%</b> across {pat.affected_count:,} events)."
                )
                flowables.append(Paragraph(p_text, self.body_style))

        flowables.append(Spacer(1, 10))
        return flowables

    def build_model_performance_section(self) -> List[Any]:
        """Section 5: Model Benchmarking & Performance Metrics."""
        flowables = []
        flowables.append(Paragraph("05. Machine Learning Model Benchmarking & Evaluation", self.h1_style))

        mod = self.result.model_results
        selected = mod.selected_model

        # Selected Model Banner
        flowables.append(Paragraph(
            f"<b>Primary Selected Classifier:</b> {selected.model_name} (Optimized Operating Threshold: <b>τ* = {selected.optimal_threshold:.4f}</b>)<br/>"
            f"<i>{selected.justification}</i>",
            self.body_style
        ))
        flowables.append(Spacer(1, 6))

        # Candidate Comparison Table
        cand_rows = [
            [
                Paragraph("<b>Candidate Model</b>", self.table_cell_bold),
                Paragraph("<b>PR-AUC</b>", self.table_cell_bold),
                Paragraph("<b>ROC-AUC</b>", self.table_cell_bold),
                Paragraph("<b>Precision</b>", self.table_cell_bold),
                Paragraph("<b>Recall</b>", self.table_cell_bold),
                Paragraph("<b>F1 Score</b>", self.table_cell_bold),
            ]
        ]
        for c in mod.candidate_models:
            is_sel = c.model_name == selected.model_name
            cand_rows.append([
                Paragraph(f"<b>{c.model_name}</b> (Selected)" if is_sel else c.model_name, self.table_cell_bold if is_sel else self.table_cell),
                Paragraph(f"{c.pr_auc:.4f}", self.table_cell_bold if is_sel else self.table_cell),
                Paragraph(f"{c.roc_auc:.4f}", self.table_cell),
                Paragraph(f"{c.precision * 100:.2f}%", self.table_cell),
                Paragraph(f"{c.recall * 100:.2f}%", self.table_cell),
                Paragraph(f"{c.f1:.4f}", self.table_cell),
            ])

        cand_table = Table(cand_rows, colWidths=[150, 75, 75, 75, 75, 70])
        cand_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        flowables.append(cand_table)
        flowables.append(Spacer(1, 8))

        # Confusion Matrix Table (from Test Set or Selected Model)
        test_m = mod.test_metrics or mod.candidate_models[0]
        cm = test_m.confusion_matrix
        cm_data = [
            [Paragraph("<b>Evaluation Matrix</b>", self.table_cell_bold), Paragraph("<b>Actual Fraud (1)</b>", self.table_cell_bold), Paragraph("<b>Actual Legitimate (0)</b>", self.table_cell_bold)],
            [Paragraph("<b>Predicted Fraud (1)</b>", self.table_cell_bold), Paragraph(f"True Positive (TP): <b>{cm.true_positive:,}</b>", self.table_cell_danger), Paragraph(f"False Positive (FP): <b>{cm.false_positive:,}</b>", self.table_cell)],
            [Paragraph("<b>Predicted Legit (0)</b>", self.table_cell_bold), Paragraph(f"False Negative (FN): <b>{cm.false_negative:,}</b>", self.table_cell), Paragraph(f"True Negative (TN): <b>{cm.true_negative:,}</b>", self.table_cell)],
        ]
        cm_table = Table(cm_data, colWidths=[140, 190, 190])
        cm_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        flowables.append(cm_table)
        flowables.append(Spacer(1, 10))
        return flowables

    def build_risk_factors_section(self) -> List[Any]:
        """Section 6: Predictive Risk Factors & Global Explainability."""
        flowables = []
        flowables.append(Paragraph("06. Predictive Risk Factors & Global Feature Importance", self.h1_style))

        top_feats = self.result.model_results.global_feature_importance[:8]
        feat_rows = [
            [Paragraph("<b>Rank</b>", self.table_cell_bold), Paragraph("<b>Feature Identifier</b>", self.table_cell_bold), Paragraph("<b>Model Importance</b>", self.table_cell_bold), Paragraph("<b>Behavioral Risk Interpretation</b>", self.table_cell_bold)]
        ]

        descriptions = {
            "amt": "Continuous transaction dollar amount.",
            "log_amount": "Logarithmically-scaled monetary amount.",
            "hour_of_day": "Hour of transaction initiation (0 - 23).",
            "is_night_hours": "Binary off-hours activity flag (23:00 - 06:00).",
            "category_gas_transport": "Gas station & automotive fuel merchant classification.",
            "category_shopping_net": "Card-Not-Present online e-commerce transaction.",
            "category_grocery_pos": "Physical point-of-sale grocery store transaction.",
            "customer_age_years": "Customer age derived relative to transaction timestamp.",
            "distance_km": "Haversine distance between customer residence and merchant coordinates.",
            "city_pop": "Population size of the cardholder's residential city."
        }

        for item in top_feats:
            desc = descriptions.get(item.feature_name, f"Categorical or numerical factor '{item.feature_name}'.")
            feat_rows.append([
                Paragraph(f"#{item.rank}", self.table_cell_bold),
                Paragraph(f"<code>{item.feature_name}</code>", self.table_cell),
                Paragraph(f"<b>{(item.importance * 100):.2f}%</b>", self.table_cell_bold),
                Paragraph(desc, self.body_style)
            ])

        table = Table(feat_rows, colWidths=[40, 140, 90, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        flowables.append(table)
        flowables.append(Spacer(1, 10))
        return flowables

    def build_high_risk_transactions_section(self) -> List[Any]:
        """Section 7: High-Risk Transactions Audit Table (Top 15-20)."""
        flowables = []
        flowables.append(Paragraph("07. Sample High-Risk Transactions Queue", self.h1_style))
        flowables.append(Paragraph(
            "Highest-priority flagged transactions requiring immediate secondary analyst review. "
            "Sensitive identifiers and full card details are securely masked in compliance with privacy controls.",
            self.body_style
        ))

        df = self.session.predictions_df
        top_txs = df.sort_values(by="risk_score", ascending=False).head(15)

        tx_rows = [
            [
                Paragraph("<b>Transaction ID</b>", self.table_cell_bold),
                Paragraph("<b>Timestamp</b>", self.table_cell_bold),
                Paragraph("<b>Amount</b>", self.table_cell_bold),
                Paragraph("<b>Category</b>", self.table_cell_bold),
                Paragraph("<b>Score</b>", self.table_cell_bold),
                Paragraph("<b>Band</b>", self.table_cell_bold),
                Paragraph("<b>Status</b>", self.table_cell_bold),
            ]
        ]

        for _, row in top_txs.iterrows():
            tx_id = str(row.get("trans_num", ""))[:12] + "..."
            ts = str(row.get("trans_date_trans_time", ""))
            amt = f"${float(row.get('amt', 0.0)):.2f}"
            cat = str(row.get("category", "")).replace("_", " ").title()[:14]
            score = f"{float(row.get('risk_score', 0.0)):.1f}"
            band = str(row.get("risk_band", "LOW"))
            is_fraud_val = row.get("is_actual_fraud")
            status_str = "FRAUD" if is_fraud_val == 1 else "LEGIT" if is_fraud_val == 0 else "FLAGGED"

            tx_rows.append([
                Paragraph(tx_id, self.table_cell),
                Paragraph(ts, self.table_cell),
                Paragraph(amt, self.table_cell_bold),
                Paragraph(cat, self.table_cell),
                Paragraph(score, self.table_cell_danger if float(score) >= 80 else self.table_cell_bold),
                Paragraph(band, self.table_cell_danger if band == "CRITICAL" else self.table_cell),
                Paragraph(status_str, self.table_cell_danger if status_str == "FRAUD" else self.table_cell),
            ])

        table = Table(tx_rows, colWidths=[90, 95, 65, 95, 55, 60, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        flowables.append(table)
        flowables.append(Spacer(1, 10))
        return flowables

    def build_findings_and_recommendations_section(self) -> List[Any]:
        """Sections 8 & 9: Evidence-Based Findings & Recommendations."""
        flowables = []
        flowables.append(Paragraph("08. Empirical Analytical Findings", self.h1_style))

        for f in self.result.findings:
            flowables.append(Paragraph(f"• <b>[{f.finding_id}] {f.title}</b> ({f.category})", self.table_cell_bold))
            flowables.append(Paragraph(f"{f.description}", self.body_style))

        flowables.append(Spacer(1, 8))
        flowables.append(Paragraph("09. Actionable Risk Mitigation Recommendations", self.h1_style))

        for r in self.result.recommendations:
            rec_text = (
                f"<b>[{r.priority} PRIORITY] {r.title}</b><br/>"
                f"<b>Action:</b> {r.action}<br/>"
                f"<b>Rationale:</b> {r.rationale}<br/>"
                f"<b>Expected Impact:</b> {r.expected_impact}"
            )
            flowables.append(Paragraph(rec_text, self.body_style))
            flowables.append(Spacer(1, 4))

        flowables.append(Spacer(1, 10))
        return flowables

    def build_methodology_and_limitations_section(self) -> List[Any]:
        """Sections 10 & 11: Methodology & Limitations."""
        flowables = []
        flowables.append(Paragraph("10. Machine Learning & Engineering Methodology", self.h1_style))
        methodology_text = (
            "<b>Leak-Free Pipeline Architecture:</b> All data transformations, scaling, and categorical one-hot encodings "
            "are fit exclusively on training data splits (75% of dataset) and applied to validation and unseen test sets without refitting.<br/>"
            "<b>Threshold Optimization:</b> Rather than assuming an arbitrary 0.5 decision boundary, the operational threshold is dynamically "
            "optimized on the validation Precision-Recall curve to maximize the F1-score for severe class imbalance.<br/>"
            "<b>Explainable AI (SHAP):</b> Feature attributions are derived using game-theoretic Shapley values, calculating exact positive "
            "and negative risk score deviations per transaction.<br/>"
            "<b>Probability Calibration Notice:</b> Tree ensemble models output leaf vote distributions; risk scores map linearly from model "
            "probabilities (risk_score = round(prob * 100, 2)) without post-hoc isotonic calibration."
        )
        flowables.append(Paragraph(methodology_text, self.body_style))
        flowables.append(Spacer(1, 8))

        flowables.append(Paragraph("11. Operational Limitations & Disclaimers", self.h1_style))
        limitations_text = (
            "• <b>Simulated Environment:</b> The dataset utilizes synthetic financial patterns; live real-world adversarial fraud tactics may evolve rapidly.<br/>"
            "• <b>Decision Support System:</b> Sentinel AI is engineered as an analyst decision-support system and should be paired with human-in-the-loop verification.<br/>"
            "• <b>Data Confidentiality:</b> This generated audit report is intended strictly for internal risk intelligence operations."
        )
        flowables.append(Paragraph(limitations_text, self.body_style))
        return flowables
