"use client";
import { Printer, Download } from "lucide-react";
export function ReportActions() {
  return (
    <div className="report-tools">
      <a className="button" href="/reports/pressure-index-report.pdf" download>
        <Download size={16} />
        Download PDF
      </a>
      <button
        className="button button-secondary"
        onClick={() => window.print()}
      >
        <Printer size={16} />
        Print / save this report
      </button>
      <p className="filter-caption">
        Same frozen rankings and evidence as the dashboard.
      </p>
    </div>
  );
}
