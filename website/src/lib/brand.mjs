// Inline copies of the brand files, recoloured with theme variables so one copy serves both themes.
import { read } from './canonical.mjs';

const themed = { '#F1F5F9': '--sl-color-white', '#14B8A6': '--site-accent', '#94A3B8': '--sl-color-gray-3' };
const inline = (name) => read(`website/public/brand/${name}-on-dark.svg`)
  .replace(/(fill|stroke)="(#[0-9A-F]{6})"/g, (_, attribute, hex) => `style="${attribute}:var(${themed[hex]})"`);

export const lockup = inline('wordmark');
export const symbol = inline('symbol');

export const colors = [
  { name: 'Canvas', hex: '#0B1017', use: 'Dark background' },
  { name: 'Surface', hex: '#141C26', use: 'Dark panels' },
  { name: 'Teal', hex: '#14B8A6', use: 'Accent on dark' },
  { name: 'Deep teal', hex: '#0F766E', use: 'Accent on light' },
  { name: 'Text', hex: '#F1F5F9', use: 'Text and mark on dark' },
  { name: 'Muted', hex: '#94A3B8', use: 'Secondary text on dark' },
  { name: 'Ink', hex: '#0F172A', use: 'Text and mark on light' },
  { name: 'Slate', hex: '#475569', use: 'Secondary text on light' },
];
