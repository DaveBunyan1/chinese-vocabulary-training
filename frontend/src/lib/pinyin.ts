/**
 * Pinyin tone-number ↔ diacritic helpers for practice UI.
 */

const TONE_MARKS: Record<string, string[]> = {
  a: ["a", "ā", "á", "ǎ", "à"],
  e: ["e", "ē", "é", "ě", "è"],
  i: ["i", "ī", "í", "ǐ", "ì"],
  o: ["o", "ō", "ó", "ǒ", "ò"],
  u: ["u", "ū", "ú", "ǔ", "ù"],
  ü: ["ü", "ǖ", "ǘ", "ǚ", "ǜ"],
  v: ["ü", "ǖ", "ǘ", "ǚ", "ǜ"],
};

const SYLLABLE_NUM = /([a-züv]+)([1-5])/gi;

function applyToneMark(syllable: string, tone: number): string {
  const lower = syllable.toLowerCase().replace(/v/g, "ü");
  for (const target of ["a", "e", "o"] as const) {
    const idx = lower.indexOf(target);
    if (idx >= 0) {
      const marks = TONE_MARKS[target];
      const mark = marks[tone] ?? target;
      return syllable.slice(0, idx) + mark + syllable.slice(idx + 1);
    }
  }
  let last = -1;
  let lastV = "";
  for (let i = 0; i < lower.length; i++) {
    if ("iuü".includes(lower[i]!)) {
      last = i;
      lastV = lower[i]!;
    }
  }
  if (last >= 0) {
    const marks = TONE_MARKS[lastV] ?? [lastV];
    const mark = marks[tone] ?? lastV;
    return syllable.slice(0, last) + mark + syllable.slice(last + 1);
  }
  return syllable;
}

/** Convert numbered pinyin to diacritics for display: `ni3 hao3` → `nǐ hǎo`. */
export function toToneMarks(pinyin: string): string {
  return pinyin.replace(SYLLABLE_NUM, (_, syl: string, tone: string) => {
    const n = Number(tone);
    if (n === 5) return syl.replace(/v/gi, "ü");
    return applyToneMark(syl, n);
  });
}

/** True when a string looks like pinyin (tone digits or Latin). */
export function looksLikePinyin(value: string): boolean {
  if (!value.trim()) return false;
  if (/[\u4e00-\u9fff]/.test(value)) return false;
  if (/[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]/.test(value)) return true;
  if (/[a-zü]+[1-5]/i.test(value)) return true;
  return /^[A-Za-züÜ\s']+$/.test(value.trim());
}

/** Format a correct-answer string for UI (diacritics when pinyin). */
export function formatAnswerForDisplay(answer: string): string {
  if (looksLikePinyin(answer) && /[1-5]/.test(answer)) {
    return toToneMarks(answer);
  }
  return answer;
}

/**
 * Expand multi-sense glosses for feedback hints.
 * `"I; me; my"` → `["I", "me", "my"]`
 */
export function expandAcceptedTerms(answers: string[]): string[] {
  const terms: string[] = [];
  for (const a of answers) {
    for (const part of a.split(/[;/]/).map((p) => p.trim()).filter(Boolean)) {
      if (!terms.includes(part)) terms.push(part);
    }
  }
  return terms;
}
