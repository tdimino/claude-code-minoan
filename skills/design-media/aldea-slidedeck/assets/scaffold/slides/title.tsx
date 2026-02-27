import React from 'react';
import { SlideLayout } from '../components';
import { TOTAL } from './constants';

export const TitleSlide = () => (
  <SlideLayout slideNumber={1} totalSlides={TOTAL} showGrid={true} showCorners={true}>
    <div className="h-full flex flex-col items-center justify-center relative">
      {/* Decorative top line */}
      <div className="w-48 h-px bg-gradient-to-r from-transparent via-[var(--blueprint-cyan)] to-transparent opacity-40 mb-8" />

      <h1 className="font-display text-5xl text-text-primary text-center leading-tight max-w-4xl">
        Presentation Title
      </h1>

      <p className="text-text-secondary text-lg mt-4 text-center max-w-2xl">
        Subtitle or tagline goes here
      </p>

      {/* Decorative bottom line */}
      <div className="w-48 h-px bg-gradient-to-r from-transparent via-[var(--blueprint-cyan)] to-transparent opacity-40 mt-8" />

      {/* Footer */}
      <div className="absolute bottom-12 flex items-center gap-3">
        <span className="font-mono text-xs text-text-muted uppercase tracking-widest">
          aldea.ai
        </span>
      </div>
    </div>
  </SlideLayout>
);
