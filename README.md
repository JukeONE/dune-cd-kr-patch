# Dune CD 한글패치

1992년 Cryo Interactive / Virgin Games의 **Dune (CD 버전)** 한글패치입니다.
DOSBox Staging으로 바로 실행되는 런처가 함께 들어 있습니다.

## 필요 사항

Dune CD 버전이 필요합니다.

## 설치

1. 이 저장소를 내려받아(Code → Download ZIP) 압축을 풉니다.
2. 안의 파일과 폴더를 모두 Dune CD 게임 폴더(`dune.dat`, `dncdprg.exe`가 있는 폴더)에 복사합니다.
3. `Korean_Install.bat`을 실행합니다.
4. `Dune_Play.bat`으로 게임을 실행합니다.
   - 처음 실행할 때 DOSBox Staging을 자동으로 내려받습니다(약 30MB, 1회).

원래대로 되돌리려면 `Korean_Restore.bat`을 실행하세요.

## 조작

| 키 | 기능 |
|---|---|
| Alt+Enter | 전체화면 전환 |
| Ctrl+F10 | 마우스 잡기/놓기 |
| Ctrl+F9 | 게임 종료 |

세이브 파일은 게임 폴더의 `SAVE\DUNECD`에 저장됩니다.

## 번역 내용

- 대사 949줄, 메뉴·UI 전체, 인트로 영상 자막, 백과사전(책) 설명문
- 인물별 말투: 레토 공작(위엄 있는 해라체), 제시카(다정한 반말), 투피르·던컨·거니(“폴 님”), 스틸가(하게체), 황제(“짐”), 하코넨(거만한 반말) 등
- 음성은 원작 영어 그대로이고, 대사창에 한국어 자막이 함께 표시됩니다.

## 글꼴

| 위치 | 글꼴 |
|---|---|
| 대사 자막 | 달무리 8px |
| 인트로 자막·오프닝 설명문 | 갈무리9 |
| 메뉴·UI | 갈무리7 |

## 동작 방식

- 원본 파일은 직접 고치지 않습니다. 설치기가 원본 `dncdprg.exe`에 패치를 적용해 `DNCDKO.EXE`를 새로 만들고, `dune.dat`에는 한글 데이터를 덧붙인 뒤 인덱스만 바꿉니다(원래 인덱스는 백업).
- 한글 출력은 게임의 글자 출력 루틴을 가로채 별도 한글 글꼴을 그리는 방식입니다. 한 음절을 2바이트로 표현해 원작의 줄바꿈·정렬 코드를 그대로 씁니다.

## 소스와 빌드

`src/` 폴더에 번역 원문(`ko/`), 빌드 도구(파이썬), 한글 출력 코드(`asm/hook.asm`, NASM)가 있습니다.

```
python src/tools/prepare.py <원본 Dune CD 폴더>   # dune.dat 추출 (패치 전 원본에서)
python src/tools/build.py                          # out/ 에 패치 파일 생성
python src/tools/mkpatch.py kopatch/patch.json     # 설치기용 차이 데이터 생성
```

번역 수정은 `src/ko/*.txt`(한 줄에 `번호 + 탭 + 문장`)를 고친 뒤 다시 빌드하면 됩니다.
`src/font/`의 갈무리 BDF는 현재 번역에 쓰인 글자만 담은 축소판입니다. 새 글자를 쓰려면 [갈무리 저장소](https://github.com/quiple/galmuri)의 `Galmuri7.bdf`, `Galmuri9.bdf`로 바꿔 주세요.
새 음절이 생기면 달무리 글자 생성에 Node.js 22 이상과 [달무리 저장소](https://github.com/RanolP/dalmoori-font)가 필요합니다(`DALMOORI_GLYPH` 환경 변수로 경로 지정).

## 크레딧

- 갈무리 글꼴 © 이민서(quiple) — SIL Open Font License 1.1 (`licenses/Galmuri-OFL.txt`)
- 달무리 글꼴 © RanolP — Apache License 2.0 (`licenses/Dalmoori-Apache-2.0.txt`)
- DOSBox Staging — 실행 시 공식 배포처에서 내려받음 (GPL-2.0)
- HSQ 형식 정보 참고: [sonicpp/Dune-game-translations](https://github.com/sonicpp/Dune-game-translations)
