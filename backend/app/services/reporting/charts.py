"""In-Memory Chart Generation Engine for Sentinel AI PDF Reports.
Renders high-resolution vector/raster figures directly to in-memory buffers
without leaving artifacts on the filesystem.
"""
import io
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless server execution
import matplotlib.pyplot as plt
import numpy as np

from ...schemas.analysis import RiskStatistics, RiskDistributionSummary, CategoricalBreakdown
from ...schemas.ml import CurvePoint


class ReportChartGenerator:
    """Generates clean, professional printable charts for PDF inclusion."""

    @classmethod
    def generate_risk_distribution_chart(cls, risk_stats: RiskStatistics) -> io.BytesIO:
        """Generates a clean donut chart for risk band proportions."""
        fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=200)

        labels = ['LOW (0-20)', 'MEDIUM (20-50)', 'HIGH (50-80)', 'CRITICAL (80-100)']
        counts = [
            risk_stats.low_risk_count,
            risk_stats.medium_risk_count,
            risk_stats.high_risk_count,
            risk_stats.critical_risk_count
        ]
        colors = ['#10B981', '#F59E0B', '#F97316', '#EF4444']

        # Donut Chart
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=labels,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 1.0 else '',
            colors=colors,
            startangle=140,
            pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor='white', linewidth=1.5),
            textprops=dict(fontsize=8, color='#1F2937')
        )

        for autotext in autotexts:
            autotext.set_fontsize(7.5)
            autotext.set_weight('bold')
            autotext.set_color('#111827')

        ax.set_title('Risk Tier Breakdown', fontsize=10, fontweight='bold', color='#111827', pad=10)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @classmethod
    def generate_category_loss_chart(cls, breakdowns: Dict[str, CategoricalBreakdown]) -> io.BytesIO:
        """Generates a horizontal bar chart of top fraud loss categories."""
        fig, ax = plt.subplots(figsize=(5.5, 3.2), dpi=200)

        sorted_cats = sorted(breakdowns.values(), key=lambda c: c.fraud_volume_usd, reverse=True)[:7]
        sorted_cats.reverse()  # For bottom-up horizontal bars

        names = [c.category_name.replace('_', ' ').title() for c in sorted_cats]
        losses = [c.fraud_volume_usd for c in sorted_cats]

        bars = ax.barh(names, losses, color='#EF4444', height=0.6, edgecolor='#DC2626', linewidth=0.8)

        ax.set_title('Top Fraud Loss by Category ($ USD)', fontsize=10, fontweight='bold', color='#111827')
        ax.set_xlabel('Fraud Exposure ($ USD)', fontsize=8, color='#4B5563')
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#D1D5DB')
        ax.spines['bottom'].set_color('#D1D5DB')
        ax.xaxis.set_major_formatter(lambda x, p: f'${int(x):,}')

        # Add values on bar ends
        for bar in bars:
            width = bar.get_width()
            ax.annotate(
                f'${int(width):,}',
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(4, 0),
                textcoords="offset points",
                ha='left', va='center',
                fontsize=7, fontweight='bold', color='#111827'
            )

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @classmethod
    def generate_score_histogram_chart(cls, risk_dist: RiskDistributionSummary) -> io.BytesIO:
        """Generates a grouped bar histogram of risk score deciles."""
        fig, ax = plt.subplots(figsize=(5.5, 3.0), dpi=200)

        x = np.arange(len(risk_dist.score_bins))
        width = 0.4

        totals = risk_dist.counts
        frauds = risk_dist.fraud_counts_per_bin

        ax.bar(x - width/2, totals, width, label='Total Volume', color='#4F46E5', edgecolor='#4338CA')
        ax.bar(x + width/2, frauds, width, label='Confirmed Fraud', color='#EF4444', edgecolor='#DC2626')

        ax.set_title('Risk Score Distribution & Fraud Concentration', fontsize=10, fontweight='bold', color='#111827')
        ax.set_xlabel('Risk Score Deciles (0 - 100)', fontsize=8, color='#4B5563')
        ax.set_ylabel('Transaction Count (Log Scale)', fontsize=8, color='#4B5563')
        ax.set_yscale('log')
        ax.set_xticks(x)
        ax.set_xticklabels(risk_dist.score_bins, fontsize=7)
        ax.tick_params(axis='y', labelsize=7)
        ax.legend(fontsize=8, frameon=False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf

    @classmethod
    def generate_pr_curve_chart(cls, pr_curve: List[CurvePoint], opt_thresh: float) -> io.BytesIO:
        """Generates a precision-recall curve with optimal decision threshold marked."""
        fig, ax = plt.subplots(figsize=(4.5, 3.0), dpi=200)

        recalls = [p.x for p in pr_curve]
        precisions = [p.y for p in pr_curve]

        ax.plot(recalls, precisions, color='#4F46E5', linewidth=1.8, label='Precision-Recall Curve')
        ax.set_title('Validation PR Curve & Threshold Optimization', fontsize=10, fontweight='bold', color='#111827')
        ax.set_xlabel('Recall (Fraud Capture Rate)', fontsize=8, color='#4B5563')
        ax.set_ylabel('Precision (Positive Accuracy)', fontsize=8, color='#4B5563')
        ax.set_xlim([0.0, 1.05])
        ax.set_ylim([0.0, 1.05])
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
