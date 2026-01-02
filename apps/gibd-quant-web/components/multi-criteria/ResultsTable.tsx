'use client';

import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  SortingState,
  ColumnDef,
  VisibilityState,
} from '@tanstack/react-table';
import { InfoTooltip } from './InfoTooltip';
import { ColumnVisibilityMenu } from './ColumnVisibilityMenu';
import type { StockResult } from '@/lib/types/query';

interface ResultsTableProps {
  results: StockResult[];
}

function formatColumnName(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }
  return String(value);
}

const columnDescriptions: Record<string, string> = {
  ticker: 'Stock symbol on Dhaka Stock Exchange',
  sector: 'Industry classification (Bank, Pharma, Telecom, etc.)',
  value: 'Primary metric value from your query (RSI, volume, price, etc.)',
  total_score: 'Combined signal score (-1 to +1): >0.4 = BUY signal, <-0.4 = SELL signal',
  rsi_contribution: 'RSI momentum indicator contribution to total score',
  trend_contribution: 'Price trend analysis contribution to total score',
  volume_contribution: 'Volume analysis contribution to total score',
  macd_contribution: 'MACD indicator contribution to total score',
};

export function ResultsTable({ results }: ResultsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(() => {
    const saved = localStorage.getItem('columnVisibility');
    return saved ? JSON.parse(saved) : {};
  });

  if (!results || results.length === 0) return null;

  const columns = useMemo(() => {
    const columnKeys = Object.keys(results[0]);
    return columnKeys.map((key) => ({
      accessorKey: key,
      header: ({ column }) => (
        <div
          onClick={column.getToggleSortingHandler()}
          className="column-header"
        >
          {formatColumnName(key)}
          {columnDescriptions[key] && (
            <InfoTooltip content={columnDescriptions[key]} />
          )}
          <span className="sort-indicator">
            {column.getIsSorted() === 'asc' && ' ▲'}
            {column.getIsSorted() === 'desc' && ' ▼'}
          </span>
        </div>
      ),
      cell: (info) => formatValue(info.getValue()),
    })) as ColumnDef<StockResult>[];
  }, [results]);

  const table = useReactTable({
    data: results,
    columns,
    state: {
      sorting,
      columnVisibility,
    },
    onSortingChange: setSorting,
    onColumnVisibilityChange: (updater) => {
      const newState =
        typeof updater === 'function' ? updater(columnVisibility) : updater;
      setColumnVisibility(newState);
      localStorage.setItem('columnVisibility', JSON.stringify(newState));
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="results-table-container">
      <div className="table-controls">
        <ColumnVisibilityMenu table={table} />
      </div>
      <table className="results-table">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
