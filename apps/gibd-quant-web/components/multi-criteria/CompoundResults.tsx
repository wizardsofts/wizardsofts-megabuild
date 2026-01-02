'use client';

import type { CompoundQueryResponse } from '@/lib/types/query';
import { ResultsTable } from './ResultsTable';
import { ExportMenu } from './ExportMenu';

interface CompoundResultsProps {
  response: CompoundQueryResponse;
  onClose: () => void;
}

export function CompoundResults({ response, onClose }: CompoundResultsProps) {
  const { criteria, individual_results, combined_results, count, match_mode, execution_time_ms } =
    response;

  return (
    <div className="compound-results-inline">
      <div className="results-header">
        <div className="results-summary">
          <span className="result-stat">
            <strong>{count}</strong> stocks · {match_mode === 'all' ? 'Match ALL' : 'Match ANY'} · {execution_time_ms.toFixed(0)}ms
          </span>
        </div>
        <div className="header-actions-right">
          <ExportMenu
            results={combined_results}
            metadata={{
              criteria: criteria.map((c) => c.query),
              matchMode: match_mode,
              resultCount: count,
              executionTime: execution_time_ms,
            }}
          />
          <button className="close-results-btn" onClick={onClose} title="Close results">
            ✕
          </button>
        </div>
      </div>


      {/* Combined Results Table */}
      {combined_results.length > 0 ? (
        <div className="results-table-section">
          <h4>Results Table:</h4>
          <ResultsTable results={combined_results} />
        </div>
      ) : (
        <div className="no-results">
          <p>No stocks match the {match_mode === 'all' ? 'ALL' : 'ANY'} criteria</p>
        </div>
      )}
    </div>
  );
}
