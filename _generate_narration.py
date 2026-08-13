"""슬라이드 내레이션 생성. ElevenLabs eleven_v3, Hyunsu 음성.

내레이션은 슬라이드 제목과 한 줄 키워드까지만 담는다. 본문은 스크린 리더가 읽으므로
같은 내용을 다시 읽으면 중복이 된다.

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
    1: "내가 만난 배리어프리 교육과 전시. 김헌용",
    2: "오늘 나눌 이야기. 네 가지",
    3: "내가 만난 세상. 자기소개 영상",
    4: "두 개의 자리. 설명을 받는 위치와 설명하는 자리",
    5: "배제하는 가이드와 포용하는 가이드",
    6: "뮤지엄 산. 낙오된 관람객",
    7: "필링 반 고흐. 시각장애인을 위한 프로그램",
    8: "나탈리의 해설. 양각 자료와 팔레트 모형",
    9: "나탈리가 한 일. 여섯 가지",
    10: "능숙하게 설명하는 가이드. 영상",
    11: "촉각 자료를 손에 쥐여 주었다. 영상",
    12: "그림 앞에 나를 앉혔다",
    13: "사람들이 모여들었다. 한 시간 사십 분",
    14: "어느 수집가의 초대. 국립중앙박물관",
    15: "전시의 설계도를 말로 건네받다",
    16: "세 곳의 차이. 전달하는 방식과 태도",
    17: "촉각 경험의 의미. 핸즈 온 익스피리언스",
    18: "촉감은 존재를 증언한다",
    19: "건축 모형. 쾰른과 안트워프",
    20: "이동에 쓰는 지도. 반 고흐 미술관 로비",
    21: "점자 범례가 붙어 있었다. 영상",
    22: "교육 시설일수록 아쉽다. 촉지도",
    23: "경기장의 소장품. 축구화",
    24: "주목할 것은 절차였다",
    25: "소리를 촉감으로 느끼다. 공간 사이",
    26: "몸으로 알게 되었다. 청음 의자와 진동",
    27: "점자가 새겨진 카드. 함께 놀 권리",
    28: "한 학생을 위한 설계, 모든 학생을 위한 수업",
    29: "설계 단계의 접근성. 포용성과 몰입감",
    30: "보편적 학습 설계와 다중 감각 구현",
    31: "워드 밤. 공강 삼십 분에 만든 어휘 게임",
    32: "픽 미. 수업 운영 도구",
    33: "학생들의 평가. 백오십오 명 익명 설문",
    34: "더 자주 하자는 응답. 구십이 점 구 퍼센트",
    35: "학습자 다양성의 증거",
    36: "전시 교육에 적용할 수 있는 다섯 가지",
    37: "다섯 가지 실천 항목",
    38: "두 가지 기술이 따로 있지 않다",
    39: "그냥 좋은 해설이었다",
    40: "마지막으로 남기고 싶은 한 문장",
    41: "공개해 둔 것. 링크 세 가지",
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
