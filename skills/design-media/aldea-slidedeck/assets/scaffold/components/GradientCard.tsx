import React from 'react';

interface GradientCardProps {
  color: string;
  icon?: React.ComponentType<any>;
  children: React.ReactNode;
  className?: string;
}

export const GradientCard: React.FC<GradientCardProps> = ({ color, icon: Icon, children, className = '' }) => (
  <div
    className={`relative rounded-xl border overflow-hidden p-6 ${className}`}
    style={{ borderColor: `${color}18`, background: `linear-gradient(135deg, ${color}06 0%, ${color}02 100%)` }}
  >
    <div className="absolute left-0 top-0 bottom-0 w-1" style={{ backgroundColor: `${color}40` }} />
    <div className="pl-2">
      {Icon && (
        <div className="w-11 h-11 rounded-lg flex items-center justify-center mb-3" style={{ backgroundColor: `${color}10` }}>
          <Icon size={24} weight="duotone" style={{ color }} />
        </div>
      )}
      {children}
    </div>
  </div>
);

export default GradientCard;
