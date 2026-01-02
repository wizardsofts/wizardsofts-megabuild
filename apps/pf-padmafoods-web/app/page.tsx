'use client';

import { useEffect } from "react";
import SnakeGame from "@/components/SnakeGame";

// Google Analytics Script
function GoogleAnalytics() {
  useEffect(() => {
    const gaId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;
    if (!gaId) return;

    const script1 = document.createElement('script');
    script1.async = true;
    script1.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`;
    document.head.appendChild(script1);

    const script2 = document.createElement('script');
    script2.innerHTML = `
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', '${gaId}');
    `;
    document.head.appendChild(script2);
  }, []);

  return null;
}

export default function ComingSoonPage() {
  return (
    <>
      <GoogleAnalytics />
      <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
        {/* Hero Section */}
        <section className="min-h-screen flex flex-col items-center justify-center px-4 py-12 gap-12">
          {/* Top Section - Centered Branding */}
          <div className="w-full text-center">
            {/* Main Heading - Script Font */}
            <h1 className="font-script text-4xl md:text-6xl text-padma-red mb-1 leading-tight">
              Padma Foods
            </h1>

            {/* Since 1995 - Script Font Subtitle */}
            <p className="font-script text-xl md:text-2xl text-padma-blue mb-6">
              Since 1995
            </p>

            {/* Quality Assured - Bold Sans-serif */}
            <h2 className="font-sans text-xl md:text-2xl font-bold text-padma-blue mb-6 tracking-wide">
              QUALITY ASSURED
            </h2>

            {/* Coming Soon Badge - BELOW QUALITY ASSURED */}
            <div className="inline-block px-6 py-2 bg-padma-red text-white rounded-full font-bold text-sm tracking-wide animate-flash">
              Coming Soon!
            </div>
          </div>

          {/* Bottom Section - Contact Box and Game Side by Side */}
          <div className="w-full flex flex-col lg:flex-row gap-8 max-w-5xl items-stretch lg:items-stretch justify-center">
            {/* Left - Contact Section */}
            <div className="w-full lg:flex-1 flex justify-center">
              <div className="bg-gradient-to-br from-padma-red to-red-700 rounded-3xl p-8 md:p-12 shadow-2xl border-4 border-padma-blue">
                <h3 className="text-white text-3xl md:text-4xl font-bold mb-2 text-center">
                  Get in Touch
                </h3>
                <p className="text-red-100 text-base mb-8 font-medium text-center">
                  Contact us to pre-order or inquire
                </p>

                {/* Phone Numbers - Large & Bold */}
                <div className="flex flex-col md:flex-row gap-4 justify-center mb-8">
                  <a
                    href="tel:+8801713492481"
                    className="inline-flex items-center justify-center gap-3 px-6 py-4 bg-white text-padma-red rounded-2xl font-bold text-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-110 active:scale-95"
                  >
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.893.953a15.13 15.13 0 006.917 6.917l.953-1.893a1 1 0 011.06-.54l4.435.74a1 1 0 01.836.986V17a2 2 0 01-2 2h-2.5a7.5 7.5 0 01-7.5-7.5V5a2 2 0 01-2-2z" />
                    </svg>
                    +880 1713-492481
                  </a>
                  <a
                    href="tel:+8801713492482"
                    className="inline-flex items-center justify-center gap-3 px-6 py-4 bg-white text-padma-red rounded-2xl font-bold text-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-110 active:scale-95"
                  >
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.893.953a15.13 15.13 0 006.917 6.917l.953-1.893a1 1 0 011.06-.54l4.435.74a1 1 0 01.836.986V17a2 2 0 01-2 2h-2.5a7.5 7.5 0 01-7.5-7.5V5a2 2 0 01-2-2z" />
                    </svg>
                    +880 1713-492482
                  </a>
                </div>

                {/* Social Links */}
                <div className="flex items-center justify-center gap-4 pt-6 border-t-2 border-white/20">
                  <span className="text-white text-sm font-semibold">Follow Us:</span>
                  <a
                    href="https://www.facebook.com/padmafoods"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center w-14 h-14 bg-white text-padma-blue rounded-full hover:shadow-2xl transition-all duration-300 transform hover:scale-125 active:scale-90"
                    title="Visit our Facebook page"
                  >
                    <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>

            {/* Right - Snake Game */}
            <div className="w-full lg:flex-1 flex flex-col items-center justify-center">
              <SnakeGame />
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-padma-dark text-white text-center py-6">
          <p className="text-sm">
            &copy; {new Date().getFullYear()} Padma Foods. All rights reserved.
          </p>
        </footer>
      </div>
    </>
  );
}
