from models.schemas import FinalReport


def generate_markdown_report(report: FinalReport) -> str:
    """Generates a formatted markdown report from the FinalReport schema."""
    lines = []
    lines.append("# Multi-Agent Code Review Report")
    lines.append(f"**File**: `{report.file_path}`")

    agreement_pct = round(report.agent_agreement * 100, 1)
    lines.append(f"**Merge Ratio (Redundancy Reduction)**: {agreement_pct}%")

    lines.append(
        f"**Overall Confidence**: {round(report.total_confidence * 100, 1)}%\n"
    )

    if not report.findings:
        lines.append("## No Issues Found 🎉")
        lines.append("All agents agreed the code looks good.")
        return "\n".join(lines)

    lines.append("## Findings\n")

    for i, finding in enumerate(report.findings, 1):
        lines.append(f"### {i}. [{finding.category.upper()}] {finding.description}")
        lines.append(
            f"**Severity**: `{finding.severity}` | "
            f"**Location**: `{finding.code_location}`"
        )
        lines.append(
            f"**Agent**: `{finding.agent_name}` | "
            f"**Confidence**: `{round(finding.confidence, 2)}`\n"
        )
        lines.append(f"{finding.explanation}\n")

    return "\n".join(lines)
