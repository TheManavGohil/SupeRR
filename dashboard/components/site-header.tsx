"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Menu, X } from "lucide-react";
import { useState } from "react";

const links = [
  ["/rankings/batting", "Selections"],
  ["/compare", "Compare"],
  ["/methodology", "Method"],
  ["/validation", "Validation"],
];
export function SiteHeader() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="site-header">
      <Link className="brand" href="/" onClick={() => setOpen(false)}>
        <span className="brand-mark" aria-hidden="true">
          P<span>↗</span>
        </span>
        <span>
          THE PRESSURE
          <br />
          <b>INDEX.</b>
        </span>
      </Link>
      <button
        className="menu-button icon-button"
        aria-label={open ? "Close navigation" : "Open navigation"}
        aria-expanded={open}
        aria-controls="site-navigation"
        onClick={() => setOpen(!open)}
      >
        {open ? <X /> : <Menu />}
      </button>
      <nav
        id="site-navigation"
        className={open ? "navigation open" : "navigation"}
        aria-label="Main navigation"
      >
        {links.map(([url, label]) => (
          <Link
            key={url}
            href={url}
            aria-current={
              path.startsWith(
                url.split("/")[1] === "rankings" ? "/rankings" : url,
              )
                ? "page"
                : undefined
            }
            onClick={() => setOpen(false)}
          >
            {label}
          </Link>
        ))}
        <Link
          className="header-report"
          href="/report"
          onClick={() => setOpen(false)}
        >
          Read report <ArrowUpRight size={14} />
        </Link>
      </nav>
    </header>
  );
}
