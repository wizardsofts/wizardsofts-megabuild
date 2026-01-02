"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

function cx(...args: Array<string | false | null | undefined>) {
  return args.filter(Boolean).join(" ");
}

export function normalizePath(p?: string | null) {
  let np = p || "/";
  // strip base locale prefix '/en' if present (keep en as default)
  if (np.startsWith("/en/")) np = np.slice(3) || "/";
  if (np === "/en") np = "/";
  // strip trailing slash (except for root)
  if (np.length > 1 && np.endsWith("/")) np = np.slice(0, -1);
  return np;
}

export function getActiveLinkFromPath(p?: string | null) {
  const pathname = normalizePath(p);
  if (pathname === "/") return "home";
  if (pathname === "/about") return "about";
  if (pathname.startsWith("/services")) return "services";
  if (pathname === "/bondwala") return "services";
  if (pathname === "/contact") return "contact";
  return "";
}

export default function Header() {
  const [open, setOpen] = useState(false);
  const [openServicesMenu, setOpenServicesMenu] = useState(false);
  const [mounted, setMounted] = useState(false);
  const rawPathname = usePathname();

  useEffect(() => {
    // mark mounted on client so we can avoid hydration mismatches by
    // rendering neutral link styles on server and only applying active
    // classes after mount
    setMounted(true);
  }, []);

  const normalize = (p?: string | null) => {
    let np = p || "/";
    // strip base locale prefix '/en' if present (keep en as default)
    if (np.startsWith("/en/")) np = np.slice(3) || "/";
    if (np === "/en") np = "/";
    // strip trailing slash (except for root)
    if (np.length > 1 && np.endsWith("/")) np = np.slice(0, -1);
    return np;
  };

  const pathname = mounted ? normalize(rawPathname) : null;
  const isServicesActive = pathname?.startsWith("/services") || pathname === "/bondwala";

  return (
    <header className="bg-white shadow-sm">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-bold text-primary">
              WizardSofts
            </Link>
          </div>

          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <Link
                href="/"
                aria-current={mounted && pathname === "/" ? "page" : undefined}
                className={
                  mounted
                    ? cx(
                        "rounded-md px-3 py-2 text-sm font-medium",
                        pathname === "/"
                          ? "bg-primary text-white hover:bg-primary-600"
                          : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                      )
                    : "rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
                }
              >
                Home
              </Link>
              <Link
                href="/about"
                aria-current={mounted && pathname === "/about" ? "page" : undefined}
                className={
                  mounted
                    ? cx(
                        "rounded-md px-3 py-2 text-sm font-medium",
                        pathname === "/about"
                          ? "bg-primary text-white hover:bg-primary-600"
                          : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                      )
                    : "rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
                }
              >
                About
              </Link>

              {/* Products & Services Dropdown */}
              <div className="relative group">
                <button
                  onMouseEnter={() => setOpenServicesMenu(true)}
                  onMouseLeave={() => setOpenServicesMenu(false)}
                  className={
                    mounted
                      ? cx(
                          "rounded-md px-3 py-2 text-sm font-medium flex items-center gap-1",
                          isServicesActive
                            ? "bg-primary text-white hover:bg-primary-600"
                            : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                        )
                      : "rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-primary flex items-center gap-1"
                  }
                >
                  Products & Services
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </button>
                {openServicesMenu && (
                  <div
                    onMouseEnter={() => setOpenServicesMenu(true)}
                    onMouseLeave={() => setOpenServicesMenu(false)}
                    className="absolute left-0 mt-0 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200"
                  >
                    <Link
                      href="/services"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary"
                    >
                      All Services
                    </Link>
                    <Link
                      href="/bondwala"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-primary"
                    >
                      BondWala
                    </Link>
                  </div>
                )}
              </div>

              <Link
                href="/contact"
                aria-current={mounted && pathname === "/contact" ? "page" : undefined}
                className={
                  mounted
                    ? cx(
                        "rounded-md px-3 py-2 text-sm font-medium",
                        pathname === "/contact"
                          ? "bg-primary text-white hover:bg-primary-600"
                          : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                      )
                    : "rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
                }
              >
                Contact
              </Link>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="inline-flex items-center justify-center rounded-md p-2 text-gray-700 hover:bg-gray-100 hover:text-primary"
              aria-expanded={open}
              aria-label="Main menu"
            >
              {open ? (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu panel */}
      {open && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link
              href="/"
              className={
                mounted
                  ? cx(
                      "block rounded-md px-3 py-2 text-base font-medium",
                      pathname === "/"
                        ? "bg-primary text-white hover:bg-primary-600"
                        : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                    )
                  : "block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
              }
              onClick={() => setOpen(false)}
            >
              Home
            </Link>
            <Link
              href="/about"
              aria-current={mounted && pathname === "/about" ? "page" : undefined}
              className={
                mounted
                  ? cx(
                      "block rounded-md px-3 py-2 text-base font-medium",
                      pathname === "/about"
                        ? "bg-primary text-white hover:bg-primary-600"
                        : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                    )
                  : "block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
              }
              onClick={() => setOpen(false)}
            >
              About
            </Link>
            <Link
              href="/services"
              className={
                mounted
                  ? cx(
                      "block rounded-md px-3 py-2 text-base font-medium",
                      pathname?.startsWith("/services")
                        ? "bg-primary text-white hover:bg-primary-600"
                        : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                    )
                  : "block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
              }
              onClick={() => setOpen(false)}
            >
              Products & Services
            </Link>
            <Link
              href="/bondwala"
              className={
                mounted
                  ? cx(
                      "block rounded-md px-3 py-2 text-base font-medium pl-6",
                      pathname === "/bondwala"
                        ? "bg-primary text-white hover:bg-primary-600"
                        : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                    )
                  : "block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-primary pl-6"
              }
              onClick={() => setOpen(false)}
            >
              BondWala
            </Link>
            <Link
              href="/contact"
              className={
                mounted
                  ? cx(
                      "block rounded-md px-3 py-2 text-base font-medium",
                      pathname === "/contact"
                        ? "bg-primary text-white hover:bg-primary-600"
                        : "text-gray-700 hover:bg-gray-100 hover:text-primary"
                    )
                  : "block rounded-md px-3 py-2 text-base font-medium text-gray-700 hover:bg-gray-100 hover:text-primary"
              }
              onClick={() => setOpen(false)}
            >
              Contact
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
