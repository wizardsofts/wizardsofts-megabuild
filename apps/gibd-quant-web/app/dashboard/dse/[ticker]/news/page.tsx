import { redirect } from 'next/navigation';

/**
 * News Page - Redirects to parent ticker page
 *
 * The News content is now rendered as a tab in the parent page.
 * This route redirects to the main ticker page.
 */

interface NewsPageProps {
  params: {
    ticker: string;
  };
}

export default async function NewsPage({ params }: NewsPageProps) {
  const { ticker } = await params;
  redirect(`/dashboard/dse/${ticker}`);
}
