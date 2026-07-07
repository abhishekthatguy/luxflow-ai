"use client";

import { useState } from "react";

type PasswordInputProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  minLength?: number;
  required?: boolean;
};

export function PasswordInput({
  id,
  label,
  value,
  onChange,
  autoComplete = "current-password",
  minLength,
  required = false,
}: PasswordInputProps) {
  const [visible, setVisible] = useState(false);

  return (
    <label htmlFor={id} className="block text-sm">
      {label}
      <div className="relative mt-1">
        <input
          id={id}
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-md border border-slate-300 py-2 pl-3 pr-10"
          autoComplete={autoComplete}
          required={required}
          minLength={minLength}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 hover:text-slate-800"
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
        >
          {visible ? (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4" aria-hidden>
              <path d="M3 3l18 18" />
              <path d="M10.58 10.58a2 2 0 0 0 2.83 2.83" />
              <path d="M9.88 4.24A10.94 10.94 0 0 1 12 4c5 0 9.27 3.11 10.5 7.5a11.62 11.62 0 0 1-1.67 3.08M6.09 6.09A11.6 11.6 0 0 0 2.5 11.5C3.73 15.89 8 19 13 19a10.9 10.9 0 0 0 4.82-1.12" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4" aria-hidden>
              <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          )}
        </button>
      </div>
    </label>
  );
}
