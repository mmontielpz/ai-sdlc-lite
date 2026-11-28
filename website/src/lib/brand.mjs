// Inline copies of the brand files, recoloured with theme variables so one copy serves both themes.
const themed = { '#F1F5F9': '--sl-color-white', '#14B8A6': '--site-accent', '#94A3B8': '--sl-color-gray-3' };
export const recolor = (svg) =>
  svg.replace(/(fill|stroke)="(#[0-9A-F]{6})"/g, (_, attribute, hex) => `style="${attribute}:var(${themed[hex]})"`);
