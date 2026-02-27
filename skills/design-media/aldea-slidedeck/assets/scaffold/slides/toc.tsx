import React from 'react';
import { SlideLayout } from '../components';
import { CH, TOTAL } from './constants';

export const TOCSlide = () => (
  <SlideLayout slideNumber={2} totalSlides={TOTAL} showGrid={true} showCorners={true}>
    <div className="h-full flex flex-col px-16 pt-14 pb-10">
      <h2 className="font-display text-4xl text-text-primary mb-2 text-center">
        What We&apos;ll Cover
      </h2>
      <p className="text-text-secondary text-base mb-8 text-center">
        Six chapters. One question.
      </p>
      <div className="grid grid-cols-3 gap-4 flex-1">
        {Object.entries(CH).map(([num, { color, icon: Icon, label }]) => {
          const descriptions: Record<string, { slides: string; firstSlide: number; desc: string }> = {
            '01': { slides: '3\u20134', firstSlide: 3, desc: 'Description for chapter one' },
            '02': { slides: '5\u20136', firstSlide: 5, desc: 'Description for chapter two' },
            '03': { slides: '7\u20138', firstSlide: 7, desc: 'Description for chapter three' },
            '04': { slides: '9\u201310', firstSlide: 9, desc: 'Description for chapter four' },
            '05': { slides: '11\u201312', firstSlide: 11, desc: 'Description for chapter five' },
            '06': { slides: '13\u201314', firstSlide: 13, desc: 'Description for chapter six' },
          };
          const info = descriptions[num];
          return (
            <div
              key={num}
              className="relative rounded-2xl border-2 overflow-hidden cursor-pointer transition-all duration-200 flex flex-col items-center text-center p-5 hover:scale-[1.02]"
              style={{
                borderColor: `${color}30`,
                background: `linear-gradient(135deg, ${color}12 0%, ${color}03 100%)`,
              }}
              onClick={() => {
                const slideEl = document.querySelectorAll('.slide')[info.firstSlide - 1];
                if (slideEl) slideEl.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-3"
                style={{ background: `${color}20` }}
              >
                <Icon size={32} weight="duotone" style={{ color }} />
              </div>
              <span className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color }}>
                {num}
              </span>
              <div className="flex-1 flex flex-col items-center justify-center">
                <h3 className="font-display text-xl font-semibold text-text-primary leading-tight">
                  {label}
                </h3>
              </div>
              <span
                className="inline-flex px-3 py-1 rounded-full text-xs font-mono mt-3"
                style={{ backgroundColor: `${color}15`, color }}
              >
                Slides {info.slides}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  </SlideLayout>
);
