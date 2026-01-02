'use client';

import { useState } from 'react';
import type { CompoundQueryCriteria } from '@/lib/types/query';

interface CriteriaBuilderProps {
  criteria: CompoundQueryCriteria[];
  onAdd: (criteria: CompoundQueryCriteria) => void;
  onRemove: (id: string) => void;
  onExecute: (matchAll: boolean) => void;
  isLoading?: boolean;
  individualResults?: Record<string, { type: string; count: number }>;
}

export function CriteriaBuilder({
  criteria,
  onAdd,
  onRemove,
  onExecute,
  isLoading,
  individualResults,
}: CriteriaBuilderProps) {
  const [input, setInput] = useState('');
  const [matchAll, setMatchAll] = useState(true);

  const handleAddCriteria = () => {
    if (input.trim() && criteria.length < 10) {
      const newCriteria: CompoundQueryCriteria = {
        id: Date.now().toString(),
        query: input.trim(),
      };
      onAdd(newCriteria);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAddCriteria();
    }
  };

  const handleExecute = () => {
    if (criteria.length > 0) {
      onExecute(matchAll);
    }
  };

  return (
    <div className="criteria-builder">
      {/* Match Mode Switch */}
      <div className="criteria-controls">
        <label className="switch">
          <input
            type="checkbox"
            checked={matchAll}
            onChange={(e) => setMatchAll(e.target.checked)}
            disabled={isLoading}
          />
          <span className="slider"></span>
          <span className="switch-label">
            Match {matchAll ? 'ALL' : 'ANY'} criteria
          </span>
        </label>
      </div>

      {/* Selected Criteria Pills */}
      {criteria.length > 0 && (
        <div className="criteria-pills">
          {criteria.map((criterion, index) => {
            const result = individualResults?.[criterion.id];
            return (
              <div key={criterion.id} className="criteria-pill">
                <span className="pill-label">
                  {index + 1}. {criterion.query}
                  {result && (
                    <span className="pill-meta">
                      {' | '}{result.type}{' | '}{result.count} result{result.count !== 1 ? 's' : ''}
                    </span>
                  )}
                </span>
                <button
                  onClick={() => onRemove(criterion.id)}
                  disabled={isLoading}
                  className="pill-remove"
                  title="Remove criterion"
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Input & Add Button - below suggestion section */}
      <div className="criteria-input-section">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g., increasing volume for 3 days"
          disabled={isLoading || criteria.length >= 10}
          className="criteria-input"
        />
        <button
          onClick={handleAddCriteria}
          disabled={!input.trim() || isLoading || criteria.length >= 10}
          className="add-criteria-btn"
        >
          {criteria.length === 10 ? 'Max criteria (10)' : 'Add'}
        </button>
        {criteria.length > 0 && (
          <button
            onClick={handleExecute}
            disabled={criteria.length === 0 || isLoading}
            className="execute-compound-btn"
          >
            {isLoading ? 'Searching...' : 'Execute'}
          </button>
        )}
      </div>
    </div>
  );
}
