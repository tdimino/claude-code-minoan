import { Globe, Cpu, WarningCircle, ChartBar, Cube, Compass } from '@phosphor-icons/react';

/** Total number of slides — update when adding/removing slides */
export const TOTAL = 10;

/**
 * Chapter definitions: color, icon, and label.
 * Colors are darkened for light-mode readability.
 * See references/design-system.md > Card Color Strategy for companion colors.
 */
export const CH: Record<string, { color: string; icon: any; label: string }> = {
  '01': { color: '#1E3A8A', icon: Globe, label: 'CHAPTER ONE' },
  '02': { color: '#D97706', icon: Cpu, label: 'CHAPTER TWO' },
  '03': { color: '#0891B2', icon: WarningCircle, label: 'CHAPTER THREE' },
  '04': { color: '#78350F', icon: ChartBar, label: 'CHAPTER FOUR' },
  '05': { color: '#059669', icon: Cube, label: 'CHAPTER FIVE' },
  '06': { color: '#7C3AED', icon: Compass, label: 'CHAPTER SIX' },
};
