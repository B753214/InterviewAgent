interface Props {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export default function Card({ children, className = "", hover = false, onClick }: Props) {
  const Component = onClick ? "button" : "div";
  return (
    <Component
      className={`w-full text-left rounded-xl border border-border bg-surface p-6 transition-all duration-150 ${
        hover ? "hover:border-ink-muted/30 hover:shadow-sm cursor-pointer" : ""
      } ${className}`}
      onClick={onClick as any}
    >
      {children}
    </Component>
  );
}
