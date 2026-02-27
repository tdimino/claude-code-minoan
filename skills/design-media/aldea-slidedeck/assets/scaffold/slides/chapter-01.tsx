import React from 'react';
import { SlideLayout } from '../components';
import { Globe } from '@phosphor-icons/react';
import { CH, TOTAL } from './constants';
import { SectionHeader, GradientCard } from './helpers';

export const Chapter01Slides = () => (
  <>
    {/* SLIDE 3: Chapter opening */}
    <SlideLayout
      chapter="01 — CHAPTER ONE"
      slideNumber={3}
      totalSlides={TOTAL}
      chapterColor={CH['01'].color}
      chapterIcon={CH['01'].icon}
    >
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <SectionHeader icon={Globe} color={CH['01'].color}>
          Section Title Here
        </SectionHeader>
        <p className="text-text-secondary text-base mb-6 text-center">
          Brief description of the section content.
        </p>
        <div className="grid grid-cols-3 gap-5 flex-1">
          {/* Use distinct colors per card in grids of 3+ */}
          <GradientCard color="#1E3A8A" icon={Globe}>
            <h3 className="text-xl font-semibold text-text-primary mb-2">Card Title</h3>
            <p className="text-text-secondary text-xs">Card body content goes here.</p>
          </GradientCard>
          <GradientCard color="#059669" icon={Globe}>
            <h3 className="text-xl font-semibold text-text-primary mb-2">Card Title</h3>
            <p className="text-text-secondary text-xs">Card body content goes here.</p>
          </GradientCard>
          <GradientCard color="#B45309" icon={Globe}>
            <h3 className="text-xl font-semibold text-text-primary mb-2">Card Title</h3>
            <p className="text-text-secondary text-xs">Card body content goes here.</p>
          </GradientCard>
        </div>
      </div>
    </SlideLayout>
  </>
);
