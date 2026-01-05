import { redirect } from 'next/navigation';

/**
 * Profile Page - Redirects to parent ticker page
 *
 * The Company Profile content is now rendered as a tab in the parent page.
 * This route redirects to the main ticker page.
 */

interface ProfilePageProps {
  params: {
    ticker: string;
  };
}

export default async function ProfilePage({ params }: ProfilePageProps) {
  const { ticker } = await params;
  redirect(`/dashboard/dse/${ticker}`);
}
