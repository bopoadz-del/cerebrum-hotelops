import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md bg-sea px-3 py-2 text-sm text-white hover:bg-sea/90 disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
