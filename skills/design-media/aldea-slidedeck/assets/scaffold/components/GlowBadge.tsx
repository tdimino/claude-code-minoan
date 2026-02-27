import React from 'react';

interface GlowBadgeProps {
  color: string;
  children: React.ReactNode;
  /** Use 'sm' for inline badges within body text, 'md' for standalone callouts */
  size?: 'sm' | 'md';
}

export const GlowBadge: React.FC<GlowBadgeProps> = ({ color, children, size = 'md' }) => (
  <span
    className={`inline-flex rounded-full font-mono font-bold ${size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-base'}`}
    style={{ backgroundColor: `${color}12`, color, boxShadow: `0 0 14px ${color}20` }}
  >
    {children}
  </span>
);

export default GlowBadge;
