"use client";

import { type ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  size?: "sm" | "md";
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-accent text-white hover:bg-accent-hover shadow-sm",
  secondary:
    "bg-surface border border-border text-ink hover:bg-surface-hover",
  ghost:
    "text-ink-muted hover:text-ink hover:bg-surface-hover",
  danger:
    "text-danger hover:bg-danger-soft",
};

const sizeClasses = {
  sm: "px-3 py-1.5 text-xs rounded-md",
  md: "px-5 py-2.5 text-sm rounded-lg",
};

export default function Button({
  variant = "primary",
  loading = false,
  size = "md",
  className = "",
  disabled,
  children,
  ...props
}: Props) {
  return (
    <button
      className={`inline-flex items-center justify-center font-medium transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 opacity-70"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
