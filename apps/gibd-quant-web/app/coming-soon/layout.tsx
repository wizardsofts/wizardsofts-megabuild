/**
 * Coming Soon Layout
 *
 * This layout provides a full-screen overlay for the coming-soon page,
 * effectively hiding the header/footer from the root layout.
 */
export default function ComingSoonLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 overflow-auto">
      {children}
    </div>
  );
}
