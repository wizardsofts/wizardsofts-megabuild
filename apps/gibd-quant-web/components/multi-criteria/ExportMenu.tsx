'use client';

import { useState } from 'react';
import { exportToCSV, exportToPDF, exportToWord } from '@/lib/utils/export';
import type { ExportMetadata } from '@/lib/utils/export';

interface ExportMenuProps {
  results: Record<string, unknown>[];
  metadata: ExportMetadata;
}

export function ExportMenu({ results, metadata }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleCSVExport = () => {
    exportToCSV(results, 'quant-flow-results.csv');
    setIsOpen(false);
  };

  const handlePDFExport = () => {
    exportToPDF(results, metadata, 'quant-flow-results.pdf');
    setIsOpen(false);
  };

  const handleWordExport = async () => {
    setIsExporting(true);
    try {
      await exportToWord(results, metadata, 'quant-flow-results.docx');
      setIsOpen(false);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="export-menu">
      <button
        className="export-menu-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="Export results"
        disabled={isExporting}
      >
        Export ▼
      </button>
      {isOpen && (
        <div className="export-dropdown">
          <button
            className="export-option"
            onClick={handleCSVExport}
            disabled={isExporting}
          >
            📊 CSV
          </button>
          <button
            className="export-option"
            onClick={handlePDFExport}
            disabled={isExporting}
          >
            📄 PDF
          </button>
          <button
            className="export-option"
            onClick={handleWordExport}
            disabled={isExporting}
          >
            📝 Word
          </button>
        </div>
      )}
    </div>
  );
}
