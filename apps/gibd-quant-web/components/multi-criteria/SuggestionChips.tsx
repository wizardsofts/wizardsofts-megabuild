'use client';

import { useState, useEffect } from 'react';
import { getSuggestions } from '@/lib/api/query';
import type { SuggestionCategory } from '@/lib/types/query';

interface SuggestionChipsProps {
  onSelect: (query: string) => void;
}

export function SuggestionChips({ onSelect }: SuggestionChipsProps) {
  const [suggestions, setSuggestions] = useState<SuggestionCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getSuggestions()
      .then((data) => {
        // Transform API response to SuggestionCategory[]
        const transformed: SuggestionCategory[] = data.examples
          ? Object.entries(data.examples).map(([category, examples]) => ({
              category,
              examples,
            }))
          : data.suggestions || [];
        setSuggestions(transformed);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error('Failed to load suggestions:', error);
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return (
      <div className="mb-6 text-center text-gray-500">
        Loading suggestions...
      </div>
    );
  }

  if (suggestions.length === 0) {
    return null;
  }

  const currentCategory = selectedCategory
    ? suggestions.find((s) => s.category === selectedCategory)
    : null;

  return (
    <div className="mb-6">
      {/* Category Chips */}
      <div className="flex flex-wrap gap-2 mb-4">
        {suggestions.map((category) => (
          <button
            key={category.category}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === category.category
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            onClick={() =>
              setSelectedCategory(
                selectedCategory === category.category ? null : category.category
              )
            }
          >
            {category.category}
          </button>
        ))}
      </div>

      {/* Example Suggestions */}
      {currentCategory && (
        <div className="flex flex-wrap gap-2">
          {currentCategory.examples.map((example) => (
            <button
              key={example}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm text-gray-700 hover:border-blue-500 hover:text-blue-600 transition-colors"
              onClick={() => onSelect(example)}
            >
              {example}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
