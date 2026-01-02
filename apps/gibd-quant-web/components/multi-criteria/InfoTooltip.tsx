'use client';
interface InfoTooltipProps {
  content: string;
}

export function InfoTooltip({ content }: InfoTooltipProps) {
  return (
    <span className="info-tooltip">
      <span className="info-icon" title={content}>ℹ️</span>
      <span className="tooltip-content">{content}</span>
    </span>
  );
}
