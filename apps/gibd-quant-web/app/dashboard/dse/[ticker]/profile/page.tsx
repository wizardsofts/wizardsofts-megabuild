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

export default function ProfilePage({ params }: ProfilePageProps) {
  redirect(`/dashboard/dse/${params.ticker}`);
}
