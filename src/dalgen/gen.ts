import { Syllable } from './core/hangul-syllable.ts';
import { readFileSync, writeFileSync } from 'fs';
const base = process.env.DALMOORI_GLYPH || '../dalmoori-font/generator/glyph';
const chars: string[] = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const L='ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ', V='ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ', T=['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
const out: Record<string,string> = {};
for (const ch of chars) {
  const c = ch.charCodeAt(0) - 0xAC00;
  const s = await Syllable.of(base, L[Math.floor(c/588)], V[Math.floor((c%588)/28)], T[c%28] || undefined);
  const g = await s.renderGlyph();
  out[ch] = (g as any).renderAsciiFont ? await (g as any).renderAsciiFont() : String(g);
}
writeFileSync(process.argv[3], JSON.stringify(out));
