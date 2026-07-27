/**
 * Unsaved workbench code, kept per problem.
 *
 * Each problem is its own route now, so wandering off to the Quest Map unmounts the editor
 * and the refetch would otherwise re-seed it from `starter_code`. sessionStorage is per-tab
 * and dies with it, so a draft also survives a reload without leaking between tabs.
 *
 * Every call is guarded: Safari in private mode throws on write, and there is no storage
 * at all during the server render.
 */

const key = (slug: string) => `windup_draft_${slug}`;

export function readDraft(slug: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(key(slug));
  } catch {
    return null;
  }
}

export function writeDraft(slug: string, code: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(key(slug), code);
  } catch {
    // Out of quota or blocked — the draft is a convenience, not something to fail over.
  }
}

export function clearDraft(slug: string): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(key(slug));
  } catch {
    // As above.
  }
}
