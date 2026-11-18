"use client";
import { CopyText } from "@/components/data-value";

import report from "@/content/generated/report.json";
import { Printer, Download } from "lucide-react";
export function ReportActions() {
  return (
    <div className="report-tools">
      {report.available && (
        <a
          className="button"
          href="/reports/pressure-index-report.pdf"
          download
        >
          <Download size={16} />
          Download PDF
        </a>
      )}
      <button
        className="button button-secondary"
        onClick={() => window.print()}
      >
        <Printer size={16} />
        Print / save this report
      </button>
      <p className="filter-caption">
        <CopyText name="reportSameRelease" />
      </p>
    </div>
  );
}
