/**
 * News Content - Tab content only
 *
 * Rendered inside the parent TickerPage's news tab
 *
 * TODO: Rebuild wizwebui library to include all exported components (Card, CardHeader, CardBody, Badge, etc.)
 * Currently the dist build is missing many components that are in the source.
 *
 * @see https://github.com/wizardsofts/wizwebui - Fix dist build exports
 */

interface NewsContentProps {
  ticker: string;
}

export default function NewsContent({ ticker }: NewsContentProps) {
  return (
    <div className="space-y-6">
      <div className="text-center py-12 text-gray-500">
        <p>News content component - Under maintenance</p>
        <p className="text-sm">Waiting for wizwebui library rebuild (missing Card, CardHeader, CardBody, Badge exports)</p>
      </div>
    </div>
  );
}
