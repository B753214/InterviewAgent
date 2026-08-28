type Tone = "neutral" | "accent" | "success" | "warning" | "danger";

interface Props {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
}

const toneClasses: Record<Tone, string> = {
  neutral: "bg-surface-raised text-ink-muted",
  accent: "bg-accent-soft text-accent",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-danger",
};

export default function Badge({ tone = "neutral", children, className = "" }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${toneClasses[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
