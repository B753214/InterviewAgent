"use client";

import { type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

const labelClass = "block text-sm font-medium text-ink-muted mb-1.5";
const baseInputClass =
  "w-full rounded-lg border border-border bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-faint focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition-colors duration-150";

export function Input({ label, className = "", ...props }: InputProps) {
  return (
    <div>
      {label && <label className={labelClass}>{label}</label>}
      <input className={`${baseInputClass} ${className}`} {...props} />
    </div>
  );
}

export function Textarea({ label, className = "", rows = 4, ...props }: TextareaProps) {
  return (
    <div>
      {label && <label className={labelClass}>{label}</label>}
      <textarea
        className={`${baseInputClass} resize-y min-h-[80px] ${className}`}
        rows={rows}
        {...props}
      />
    </div>
  );
}
