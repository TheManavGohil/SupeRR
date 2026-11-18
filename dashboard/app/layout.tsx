import { CopyText } from "@/components/data-value";
import { copy } from "@/content/copy";
import site from "@/content/generated/site.json";
import type { Metadata } from "next";
import localFont from "next/font/local";
import Link from "next/link";
import { SiteHeader } from "@/components/site-header";
import { ArrowUpRight } from "lucide-react";
import "./globals.css";

const headingFont = localFont({
  src: [
    {
      path: "../public/fonts/barlow-condensed-latin-500-normal.woff2",
      weight: "500",
      style: "normal",
    },
    {
      path: "../public/fonts/barlow-condensed-latin-600-normal.woff2",
      weight: "600",
      style: "normal",
    },
  ],
  variable: "--font-heading",
  display: "swap",
  adjustFontFallback: "Arial",
});
const readingFont = localFont({
  src: "../public/fonts/manrope-latin-wght-normal.woff2",
  weight: "200 800",
  variable: "--font-reading",
  display: "swap",
  adjustFontFallback: "Arial",
});

export const metadata: Metadata = {
  title: {
    default: "The Pressure Index — Evidence behind every pick",
    template: "%s · The Pressure Index",
  },
  description: copy.metadataDescription,
  metadataBase: new URL(site.publicBaseUrl),
  robots: { index: false, follow: false },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${headingFont.variable} ${readingFont.variable}`}
    >
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main">{children}</main>
        <footer className="site-footer">
          <div>
            <Link className="footer-title" href="/">
              THE PRESSURE INDEX<span>↗</span>
            </Link>
            <p>
              <CopyText name="footer" />
            </p>
            <p>
              <CopyText name="authorship" />
            </p>
          </div>
          <div>
            <Link href="/methodology">
              Understand the method <ArrowUpRight size={14} />
            </Link>
            <Link href="/report">
              Read the complete report <ArrowUpRight size={14} />
            </Link>
            <small>
              <CopyText name="footerScope" />
            </small>
          </div>
        </footer>
      </body>
    </html>
  );
}
