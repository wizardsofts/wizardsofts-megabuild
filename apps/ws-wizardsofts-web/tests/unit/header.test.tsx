import { normalizePath, getActiveLinkFromPath } from '@/components/Header';

describe('Header active link logic (unit)', () => {
  it('returns contact for /contact', () => {
    expect(getActiveLinkFromPath('/contact')).toBe('contact');
  });

  it('returns about for /about (negative/other path)', () => {
    expect(getActiveLinkFromPath('/about')).toBe('about');
    expect(getActiveLinkFromPath('/something-else')).toBe('');
  });

  it('returns services for nested /services/* paths (edge case)', () => {
    expect(getActiveLinkFromPath('/services')).toBe('services');
    expect(getActiveLinkFromPath('/services/custom-erp')).toBe('services');
  });

  it('normalizes trailing slash and locale /en prefix', () => {
    expect(normalizePath('/contact/')).toBe('/contact');
    expect(normalizePath('/en/contact')).toBe('/contact');
    expect(normalizePath('/en')).toBe('/');
  });
});
