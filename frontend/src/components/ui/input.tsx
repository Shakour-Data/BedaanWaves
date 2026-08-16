import { type InputHTMLAttributes } from "react";

export function Input({ className, type, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={className}
      {...props}
    />
  );
}