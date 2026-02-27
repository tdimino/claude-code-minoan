import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface ImageLightboxProps {
  src: string;
  alt: string;
  caption?: string;
  className?: string;
  thumbnailClassName?: string;
}

export function ImageLightbox({
  src,
  alt,
  caption,
  className = '',
  thumbnailClassName = '',
}: ImageLightboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);

  const openLightbox = () => setIsOpen(true);
  const closeLightbox = () => {
    setIsZoomed(false);
    setIsOpen(false);
  };
  const toggleZoom = () => setIsZoomed((prev) => !prev);

  return (
    <>
      {/* Thumbnail */}
      <div className={`relative group cursor-pointer ${className}`} onClick={openLightbox}>
        <img
          src={src}
          alt={alt}
          className={`w-full h-full object-cover transition-all duration-300 group-hover:scale-[1.02] ${thumbnailClassName}`}
        />
        <div className="absolute inset-0 bg-blueprint-dark/0 group-hover:bg-blueprint-dark/20 transition-colors duration-300 flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <svg
              className="w-10 h-10 text-blueprint-cyan drop-shadow-lg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"
              />
            </svg>
          </div>
        </div>
        {caption && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-blueprint-dark/90 to-transparent p-3 pt-8">
            <p className="font-mono text-xs text-text-secondary">{caption}</p>
          </div>
        )}
      </div>

      {/* Lightbox Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Backdrop */}
            <motion.div
              className="absolute inset-0 bg-blueprint-dark/95 backdrop-blur-sm"
              onClick={closeLightbox}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            />

            {/* Close button */}
            <button
              onClick={closeLightbox}
              className="absolute top-6 right-6 z-10 p-2 text-text-secondary hover:text-text-primary transition-colors"
            >
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Zoom toggle */}
            <button
              onClick={toggleZoom}
              className="absolute top-6 right-20 z-10 p-2 text-text-secondary hover:text-text-primary transition-colors"
            >
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isZoomed ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                )}
              </svg>
            </button>

            {/* Image container */}
            <motion.div
              className={`relative z-10 ${isZoomed ? 'cursor-zoom-out overflow-auto max-h-[90vh] max-w-[90vw]' : 'cursor-zoom-in'}`}
              onClick={toggleZoom}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.25, 0.4, 0.25, 1] }}
            >
              <img
                src={src}
                alt={alt}
                className={`${
                  isZoomed
                    ? 'max-w-none'
                    : 'max-w-[85vw] max-h-[80vh] object-contain'
                } rounded-lg shadow-2xl border border-blueprint-grid/30`}
                style={isZoomed ? { transform: 'scale(1.5)', transformOrigin: 'center' } : undefined}
              />
            </motion.div>

            {/* Caption */}
            {caption && (
              <motion.div
                className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ delay: 0.1 }}
              >
                <p className="font-mono text-sm text-text-secondary bg-blueprint-dark/80 px-4 py-2 rounded-lg border border-blueprint-grid/30 backdrop-blur-sm">
                  {caption}
                </p>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Gallery component for multiple images
interface ImageGalleryProps {
  images: { src: string; alt: string; caption?: string }[];
  columns?: 2 | 3 | 4;
  gap?: 'sm' | 'md' | 'lg';
}

export function ImageGallery({ images, columns = 3, gap = 'md' }: ImageGalleryProps) {
  const gapClass = { sm: 'gap-2', md: 'gap-4', lg: 'gap-6' }[gap];
  const colClass = { 2: 'grid-cols-2', 3: 'grid-cols-3', 4: 'grid-cols-4' }[columns];

  return (
    <div className={`grid ${colClass} ${gapClass}`}>
      {images.map((image, index) => (
        <ImageLightbox
          key={index}
          src={image.src}
          alt={image.alt}
          caption={image.caption}
          className="aspect-video rounded-lg overflow-hidden border border-blueprint-grid/30"
        />
      ))}
    </div>
  );
}
