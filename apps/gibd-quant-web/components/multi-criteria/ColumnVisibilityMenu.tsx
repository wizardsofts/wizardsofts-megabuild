'use client';

import { useState } from 'react';
import type { Table } from '@tanstack/react-table';
import type { StockResult } from '@/lib/types/query';

interface ColumnVisibilityMenuProps {
  table: Table<StockResult>;
}

export function ColumnVisibilityMenu({ table }: ColumnVisibilityMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="column-visibility-menu">
      <button
        className="column-menu-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="Toggle column visibility"
      >
        Columns ▼
      </button>
      {isOpen && (
        <div className="column-dropdown">
          {table.getAllLeafColumns().map((column) => (
            <label key={column.id} className="column-option">
              <input
                type="checkbox"
                checked={column.getIsVisible()}
                onChange={column.getToggleVisibilityHandler()}
              />
              <span className="column-name">
                {column.columnDef.header
                  ? typeof column.columnDef.header === 'string'
                    ? column.columnDef.header
                    : column.id
                  : column.id}
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
