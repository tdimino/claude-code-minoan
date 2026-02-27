import React from 'react';

interface SectionHeaderProps {
  icon: React.ComponentType<any>;
  color: string;
  children: React.ReactNode;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ icon: Icon, color, children }) => (
  <div className="flex flex-col items-center gap-3 mb-6">
    <div className="flex items-center gap-3">
      <div className="w-12 h-px" style={{ background: `linear-gradient(to right, transparent, ${color}40)` }} />
      <Icon size={26} weight="duotone" style={{ color }} />
      <div className="w-12 h-px" style={{ background: `linear-gradient(to left, transparent, ${color}40)` }} />
    </div>
    <h2 className="font-display text-4xl text-text-primary text-center">{children}</h2>
  </div>
);

export default SectionHeader;
