"use client";

interface Tab {
  key: string;
  label: string;
}

interface Props {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
  className?: string;
}

export default function Tabs({ tabs, active, onChange, className = "" }: Props) {
  return (
    <div className={`flex gap-0.5 p-0.5 rounded-lg bg-surface-raised ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150 ${
            active === tab.key
              ? "bg-surface text-ink shadow-sm"
              : "text-ink-muted hover:text-ink"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
