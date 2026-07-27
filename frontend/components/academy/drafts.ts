/**
 * Unsaved workbench code, kept per problem and per language.
 *
 * Each problem is its own route now, so wandering off to the Quest Map unmounts the editor
 * and the refetch would otherwise re-seed it from `starter_code`. sessionStorage is per-tab
 * and dies with it, so a draft also survives a reload without leaking between tabs.
 *
 * The language is part of the key because a half-written Python attempt and a half-written
 * JavaScript one are both worth keeping — switching benches to compare the two stubs should
 * not throw either of them away.
 *
 * Every call is guarded: Safari in private mode throws on write, and there is no storage
 * at all during the server render.
 */

const key = (slug: string, language: string) => `windup_draft_${slug}__${language}`;

export function readDraft(slug: string, language: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(key(slug, language));
  } catch {
    return null;
  }
}

export function writeDraft(slug: string, language: string, code: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(key(slug, language), code);
  } catch {
    // Out of quota or blocked — the draft is a convenience, not something to fail over.
  }
}

export function clearDraft(slug: string, language: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(key(slug, language));
  } catch {
    // As above.
  }
}
