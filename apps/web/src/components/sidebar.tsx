"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  {
    href: "/",
    label: "首页",
    icon: (active: boolean) => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.2" />
        <rect x="14" y="3" width="7" height="7" rx="1.2" />
        <rect x="3" y="14" width="7" height="7" rx="1.2" />
        <rect x="14" y="14" width="7" height="7" rx="1.2" />
      </svg>
    ),
  },
  {
    href: "/profile",
    label: "我的档案",
    icon: (active: boolean) => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
      </svg>
    ),
  },
  {
    href: "/interview",
    label: "模拟面试",
    icon: (active: boolean) => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="5,3 19,12 5,21" />
      </svg>
    ),
  },
  {
    href: "/history",
    label: "面试历史",
    icon: (active: boolean) => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <polyline points="12,6 12,12 16,14" />
      </svg>
    ),
  },
  {
    href: "/skills",
    label: "能力图谱",
    icon: (active: boolean) => (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" />
        <line x1="12" y1="22" x2="12" y2="15.5" />
        <polyline points="22,8.5 12,15.5 2,8.5" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-sidebar flex flex-col select-none z-50">
      {/* Logo */}
      <div className="px-4 pt-6 pb-5 border-b border-sidebar-border">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
            <span className="text-white text-sm font-bold">IA</span>
          </div>
          <div>
            <div className="text-sm font-semibold text-sidebar-text-active leading-tight">Interview</div>
            <div className="text-[11px] text-sidebar-text leading-tight">Agent Platform</div>
          </div>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item, i) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                active
                  ? "bg-sidebar-active text-sidebar-text-active shadow-sm ring-1 ring-white/5"
                  : "text-sidebar-text hover:bg-sidebar-hover hover:text-sidebar-text-active"
              }`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <span className={active ? "text-sidebar-accent" : "opacity-50"}>
                {item.icon(active)}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center text-[10px] font-bold text-sidebar-accent">
            U
          </div>
          <div className="text-xs text-sidebar-text">单用户模式</div>
        </div>
      </div>
    </aside>
  );
}
