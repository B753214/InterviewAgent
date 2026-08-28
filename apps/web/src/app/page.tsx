import Link from "next/link";

const SECTIONS = [
  {
    href: "/profile",
    title: "我的档案",
    desc: "管理简历画像、岗位画像与面试参考资料",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
      </svg>
    ),
  },
  {
    href: "/interview",
    title: "模拟面试",
    desc: "选择画像与资料，开启 AI 驱动的实战对练",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="5,3 19,12 5,21" />
      </svg>
    ),
  },
  {
    href: "/history",
    title: "面试历史",
    desc: "回顾过往面试记录与详细评估报告",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <polyline points="12,6 12,12 16,14" />
      </svg>
    ),
  },
  {
    href: "/skills",
    title: "能力图谱",
    desc: "追踪知识点掌握度，发现薄弱环节针对性提升",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" />
        <line x1="12" y1="22" x2="12" y2="15.5" />
        <polyline points="22,8.5 12,15.5 2,8.5" />
      </svg>
    ),
  },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <div className="mb-10 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-soft text-accent text-xs font-medium mb-5">
          AI-Powered Mock Interview
        </div>
        <h1 className="text-3xl font-bold text-ink tracking-tight mb-3">
          智能模拟面试系统
        </h1>
        <p className="text-ink-muted text-sm leading-relaxed max-w-md mx-auto">
          基于 LangGraph + RAG + 长期记忆的多画像面试对练平台，帮助你精准备战，持续提升
        </p>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 stagger">
        {SECTIONS.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="group relative rounded-xl border border-border bg-surface p-5 hover:border-accent-muted hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-lg bg-accent-soft text-accent flex items-center justify-center group-hover:bg-accent group-hover:text-white transition-colors duration-200">
                {s.icon}
              </div>
              <h2 className="font-semibold text-ink">{s.title}</h2>
            </div>
            <p className="text-sm text-ink-muted leading-relaxed">{s.desc}</p>
            <div className="absolute top-5 right-5 w-6 h-6 rounded-full border border-border flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200 translate-x-1 group-hover:translate-x-0">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-ink-muted">
                <polyline points="9,5 16,12 9,19" />
              </svg>
            </div>
          </Link>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-border-light text-center">
        <p className="text-xs text-ink-faint">
          LangGraph 编排 · RAG 知识检索 · 长期记忆追踪 · 多画像对练
        </p>
      </div>
    </div>
  );
}
