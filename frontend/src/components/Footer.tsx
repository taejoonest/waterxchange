import Link from "next/link";
import Image from "next/image";

const columns = [
  {
    title: "Platform",
    links: [
      { label: "Monitoring", href: "/monitoring" },
      { label: "Transfer", href: "/transfer" },
      { label: "Hardware", href: "/hardware" },
      { label: "iOS App", href: "#" },
    ],
  },
  {
    title: "Technology",
    links: [
      { label: "SGMA Compliance", href: "#" },
      { label: "Knowledge Graph", href: "#" },
      { label: "Open Source HW", href: "/hardware" },
      { label: "Documentation", href: "#" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Kern County GSP", href: "#" },
      { label: "SGMA Overview", href: "#" },
      { label: "API Reference", href: "#" },
      { label: "Contact", href: "mailto:contact@waterxchange.io" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-12 md:grid-cols-4">
          <div>
            <Link href="/" className="flex items-center gap-2.5">
              <Image src="/logo.png" alt="WaterXchange" width={54} height={30} className="h-8 w-auto" />
              <span className="text-xl font-bold tracking-tight text-navy">
                Water<span className="text-teal">X</span>change
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-gray-500">
              Smart water trading for California farmers. SGMA-compliant, AI-powered, open-source hardware.
            </p>
          </div>
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="mb-4 text-xs font-bold uppercase tracking-widest text-gray-400">
                {col.title}
              </h4>
              <ul className="space-y-3">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 transition-colors hover:text-teal"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-gray-100 pt-8 md:flex-row">
          <p className="text-sm text-gray-400">
            &copy; 2026 WaterXchange. Built for California&apos;s water future.
          </p>
          <div className="flex gap-6">
            <a href="#" className="text-sm text-gray-400 hover:text-teal">Terms</a>
            <a href="#" className="text-sm text-gray-400 hover:text-teal">Privacy</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
