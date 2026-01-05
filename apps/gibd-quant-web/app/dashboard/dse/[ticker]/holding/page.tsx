import { redirect } from 'next/navigation';

/**
 * Holdings Page - Redirects to parent ticker page
 *
 * The Holdings content is now rendered as a tab in the parent page.
 * This route redirects to the main ticker page.
 */

interface HoldingsPageProps {
  params: {
    ticker: string;
  };
}

export default function HoldingsPage({ params }: HoldingsPageProps) {
  redirect(`/dashboard/dse/${params.ticker}`);
}
