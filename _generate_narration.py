"""슬라이드 내레이션 생성. ElevenLabs eleven_v3, Hyunsu 음성.

이 덱의 내레이션은 발표자가 진행 상태를 귀로 확인하는 큐다. 청중에 시각장애인이 없어
전 슬라이드에 두지 않고 구조가 바뀌는 자리에만 둔다. 표지, 장 표지 넷, 제언 다섯,
나가며, 마지막 문장이다. 문안은 제목까지만 담는다.

대상 슬라이드 번호는 세 곳에 같이 적혀 있다. 여기 NARRATIONS의 키, index.html의
NARRATED 배열, .deck-check.json의 narration이다. 하나를 고치면 셋을 함께 고친다.

약어·영문 표기·숫자는 TTS가 철자를 그대로 읽어 버리므로 한글 발음으로 적는다
(txt는 "티엑스티", AI는 "에이아이", 제45차는 "제 사십오차").

문안이 짧으면 음량이 떨어진다. 세 글자로 뽑았다가 0.56초에 최대 -9.7 dB로 나온 적이
있다. 제목이 짧은 장은 키워드 한 줄을 붙여 2초 이상으로 만든다.

    python _generate_narration.py            # 없는 것만 생성
    python _generate_narration.py --force    # 전부 다시 생성

생성 후 기준선(.narration-manifest.json)을 자동으로 갱신한다. 이 파일이 있어야
검증 스크립트가 "문안을 고쳐 놓고 다시 뽑지 않은 트랙"을 잡아낸다. 파일 시각으로는
판별되지 않는다. 스크립트를 한 줄만 고쳐도 모든 트랙이 오래된 것으로 보이기 때문이다.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

VOICE_ID = "cuXUjH0CSJkKipo0Hy9i"  # Hyunsu: 한국어 남성, 팟캐스트 진행 톤
MODEL_ID = "eleven_v3"
OUT_DIR = Path(__file__).parent / "narration"
MANIFEST = OUT_DIR / ".narration-manifest.json"

NARRATIONS = {
    1: "내가 만난 배리어프리 교육과 전시",
    6: "배제하는 가이드와 포용하는 가이드",
    18: "촉각 경험의 의미",
    30: "한 학생을 위한 설계, 모든 학생을 위한 수업",
    38: "생물다양성교실에 적용할 수 있는 다섯 가지",
    39: "하나. 교육 시작 전에 먼저 물어보세요",
    40: "둘. 준비한 것은 빠짐없이 말로 설명해 주세요",
    41: "셋. 화면 속 모양을 몸으로 따라 하게 해 주세요",
    42: "넷. 활동을 바꾸지 말고 순서를 하나만 더 넣어 주세요",
    43: "다섯. 만져도 되는 표본을 미리 골라 알려 주세요",
    45: "두 가지 기술이 따로 있지 않다",
    47: "마지막으로 남기고 싶은 한 문장",
}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_manifest():
    """지금 있는 mp3가 지금 문안으로 만들어졌다고 기록한다."""
    data = {str(n): digest(t) for n, t in NARRATIONS.items()
            if (OUT_DIR / f"slide-{n:02d}.mp3").exists()}
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(data)


def main():
    force = "--force" in sys.argv

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY env var not set")

    from elevenlabs import ElevenLabs, VoiceSettings

    client = ElevenLabs(api_key=api_key)
    OUT_DIR.mkdir(exist_ok=True)

    made = 0
    for num, text in sorted(NARRATIONS.items()):
        mp3_path = OUT_DIR / f"slide-{num:02d}.mp3"
        if mp3_path.exists() and not force:
            print(f"[{num:02d}] skip (exists)")
            continue

        print(f"[{num:02d}] {text}")
        audio = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            text=text,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
                speed=1.0,
            ),
        )
        mp3_path.write_bytes(b"".join(audio))
        made += 1

    n = write_manifest()
    print(f"\nDone. {made} generated, {len(NARRATIONS) - made} skipped. 기준선 {n}개 기록.")
    print("길이와 음량은 check_audio.py로 확인한다.")


if __name__ == "__main__":
    main()
