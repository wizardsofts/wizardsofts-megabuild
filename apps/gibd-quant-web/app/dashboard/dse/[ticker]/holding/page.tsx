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

export default async function HoldingsPage({ params }: HoldingsPageProps) {
  const { ticker } = await params;
  redirect(`/dashboard/dse/${ticker}`);
}
