'use client';

import './multi-criteria-styles.css';
import { useState } from 'react';
import { CriteriaBuilder } from '@/components/multi-criteria/CriteriaBuilder';
import { CompoundResults } from '@/components/multi-criteria/CompoundResults';
import { SuggestionChips } from '@/components/multi-criteria/SuggestionChips';
import { executeCompoundQuery } from '@/lib/api/query';
import type { CompoundQueryCriteria, CompoundQueryResponse } from '@/lib/types/query';

/**
 * Multi-Criteria Query Page
 *
 * Allows users to build complex queries by combining multiple criteria with AND/OR logic.
 * Features include:
 * - Add/remove multiple query criteria
 * - Toggle between AND (match all) and OR (match any) modes
 * - View individual and combined results
 * - Export results to CSV, PDF, or Word
 * - Column visibility management
 * - Sortable result tables
 */
export default function MultiCriteriaPage() {
  const [criteria, setCriteria] = useState<CompoundQueryCriteria[]>([]);
  const [compoundResults, setCompoundResults] = useState<CompoundQueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAddCriteria = (newCriteria: CompoundQueryCriteria) => {
    setCriteria([...criteria, newCriteria]);
  };

  const handleRemoveCriteria = (id: string) => {
    setCriteria(criteria.filter((c) => c.id !== id));
  };

  const handleExecuteCompound = async (matchAll: boolean) => {
    setIsLoading(true);
    try {
      const response = await executeCompoundQuery({
        criteria,
        match_all: matchAll,
        limit: 50,
      });
      setCompoundResults(response);
    } catch (error) {
      console.error('Compound query failed:', error);
      alert(`Failed to execute compound query: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseResults = () => {
    setCompoundResults(null);
  };

  const handleSuggestionSelect = (suggestion: string) => {
    handleAddCriteria({
      id: Date.now().toString(),
      query: suggestion,
    });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Multi-Criteria Stock Query
          </h1>
          <p className="text-gray-600">
            Build complex queries by combining multiple criteria with AND/OR logic
          </p>
        </div>

        {/* Suggestion Chips */}
        <SuggestionChips onSelect={handleSuggestionSelect} />

        {/* Criteria Builder */}
        <CriteriaBuilder
          criteria={criteria}
          onAdd={handleAddCriteria}
          onRemove={handleRemoveCriteria}
          onExecute={handleExecuteCompound}
          isLoading={isLoading}
          individualResults={compoundResults?.individual_results}
        />

        {/* Results */}
        {compoundResults && (
          <div className="mt-8">
            <CompoundResults
              response={compoundResults}
              onClose={handleCloseResults}
            />
          </div>
        )}
      </div>
    </div>
  );
}
