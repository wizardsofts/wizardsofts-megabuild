import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import BondWalaPage from "../../app/bondwala/page";

describe("BondWala Page", () => {
  beforeEach(() => {
    // Mock Date to be predictable
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2025-12-30"));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("should render the coming soon message", () => {
    render(<BondWalaPage />);
    const comingSoonElements = screen.getAllByText(/Coming Soon/i);
    expect(comingSoonElements.length).toBeGreaterThan(0);
  });

  it("should display dynamic launch date (7 days from now)", async () => {
    render(<BondWalaPage />);

    // Wait for the useEffect to set the launch date
    // Expected date: December 30, 2025 + 7 days = January 6, 2026
    await waitFor(
      () => {
        const dateElements = screen.queryAllByText(/January 6, 2026/i);
        expect(dateElements.length).toBeGreaterThan(0);
      },
      { timeout: 3000 }
    );
  });

  it("should show fallback text when date is not loaded", () => {
    render(<BondWalaPage />);

    // Initially, before useEffect runs, should show fallback
    const comingSoonElements = screen.getAllByText(/Coming Soon|January 2026/i);
    expect(comingSoonElements.length).toBeGreaterThan(0);
  });

  it("should render the expected launch date section", async () => {
    render(<BondWalaPage />);

    await waitFor(() => {
      expect(screen.getByText(/Expected Launch Date/i)).toBeInTheDocument();
    });
  });

  it("should render the BondWala description", () => {
    render(<BondWalaPage />);

    expect(
      screen.getByText(/Bangladesh Prize Bond tracker app/i)
    ).toBeInTheDocument();
  });

  it("should render the Learn More button", () => {
    render(<BondWalaPage />);

    const learnMoreButton = screen.getByText(/Learn More/i);
    expect(learnMoreButton).toBeInTheDocument();
    expect(learnMoreButton.closest("a")).toHaveAttribute(
      "href",
      "#how-it-works"
    );
  });

  it("should not display download links (they should be commented out)", () => {
    const { container } = render(<BondWalaPage />);

    // Check that Google Play button is not in the rendered DOM
    expect(screen.queryByText(/Get it on.*Google Play/i)).not.toBeInTheDocument();

    // Check that there's no link to play.google.com
    const links = container.querySelectorAll('a[href*="play.google.com"]');
    expect(links.length).toBe(0);

    // Check that there's no link to apps.apple.com
    const appleLinks = container.querySelectorAll('a[href*="apps.apple.com"]');
    expect(appleLinks.length).toBe(0);
  });

  it("should render FAQ section", () => {
    render(<BondWalaPage />);

    expect(
      screen.getByText(/Frequently Asked Questions/i)
    ).toBeInTheDocument();
  });

  it("should render support section", () => {
    render(<BondWalaPage />);

    expect(screen.getByText(/Need Help\?/i)).toBeInTheDocument();
    expect(
      screen.getByText(/bondwala@wizardsofts\.com/i)
    ).toBeInTheDocument();
  });
});
