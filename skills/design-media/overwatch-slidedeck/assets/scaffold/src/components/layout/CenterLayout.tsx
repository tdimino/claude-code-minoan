import type { ReactNode } from "react";

interface CenterLayoutProps {
  children: ReactNode;
  className?: string;
}

export function CenterLayout({ children, className = "" }: CenterLayoutProps) {
  return (
    <div className={`flex flex-col items-center justify-center h-full text-center ${className}`}>
      {children}
    </div>
  );
}
