import React from 'react';

interface SlideLayoutProps {
  children: React.ReactNode;
  chapter?: string;
  slideNumber?: number;
  totalSlides?: number;
  showGrid?: boolean;
  showCorners?: boolean;
  chapterColor?: string;   // Dynamic chapter accent (e.g., '#1E3A8A')
  chapterIcon?: React.ComponentType<any>;  // Optional chapter icon for badge
}

export const SlideLayout: React.FC<SlideLayoutProps> = ({
  children,
  chapter,
  slideNumber,
  totalSlides,
  showGrid = true,
  showCorners = true,
  chapterColor,
  chapterIcon: ChapterIcon,
}) => {
  return (
    <div
      className={`slide relative ${showGrid ? 'blueprint-grid' : ''} ${showCorners ? 'corner-marks' : ''}`}
      style={{
        background: 'var(--canvas-900)',
        // Dynamic corner color from chapter accent
        ...(chapterColor ? { '--corner-color': `${chapterColor}60` } as React.CSSProperties : {}),
      }}
    >
      {/* Fine grid overlay */}
      {showGrid && (
        <div className="absolute inset-0 blueprint-grid-fine pointer-events-none" />
      )}

      {/* Chapter badge - top left */}
      {chapter && (
        <div className="absolute top-8 left-10 flex items-center gap-2">
          {ChapterIcon && (
            <ChapterIcon size={14} weight="duotone" style={{ color: chapterColor || 'var(--blueprint-cyan)' }} />
          )}
          <span
            className="chapter-badge"
            style={chapterColor ? {
              color: chapterColor,
              background: `${chapterColor}08`,
              borderColor: `${chapterColor}20`,
            } : {}}
          >
            {chapter}
          </span>
        </div>
      )}

      {/* Aldea logo - top right
          Light mode: use aldea-logo-black.png
          Dark mode: use aldea-logo.png with brightness filter */}
      <div className="absolute top-6 right-10 flex items-center gap-2">
        <img
          src="/images/aldea-logo-black.png"
          alt="Aldea"
          className="h-8"
        />
      </div>

      {/* Main content */}
      <div className="relative z-10 h-full">
        {children}
      </div>

      {/* Slide number - top right, below logo */}
      {slideNumber && (
        <div className="absolute top-16 right-10">
          <span className="font-mono text-xs text-text-muted">
            {String(slideNumber).padStart(2, '0')} / {totalSlides ?? '??'}
          </span>
        </div>
      )}

      {/* Decorative bottom line — uses chapter color when available */}
      <div
        className="absolute bottom-0 left-0 right-0 h-[2px]"
        style={{
          background: chapterColor
            ? `linear-gradient(to right, transparent, ${chapterColor}30, transparent)`
            : 'linear-gradient(to right, transparent, var(--blueprint-cyan), transparent)',
          opacity: 0.3,
        }}
      />
    </div>
  );
};

export default SlideLayout;
