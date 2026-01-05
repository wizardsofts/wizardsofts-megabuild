/**
 * Holdings Content - Tab content only
 *
 * Rendered inside the parent TickerPage's holdings tab
 *
 * TODO: Rebuild wizwebui library to include all exported components (Table, Card, Badge, etc.)
 * Currently the dist build is missing many components that are in the source.
 *
 * @see https://github.com/wizardsofts/wizwebui - Fix dist build exports
 */

interface HoldingContentProps {
  ticker: string;
}

export default function HoldingContent({ ticker }: HoldingContentProps) {
  return (
    <div className="space-y-6">
      <div className="text-center py-12 text-gray-500">
        <p>Holdings data component - Under maintenance</p>
        <p className="text-sm">Waiting for wizwebui library rebuild (missing Table, Card, Badge exports)</p>
      </div>
    </div>
  );
}
