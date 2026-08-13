"""슬라이드 텍스트만 뽑아 점자정보단말기용 txt로 만든다.

발표 중에 한소네로 훑어보는 자료다. 그래서 구분선도 머리말도 넣지 않고 슬라이드에
있는 텍스트만 화면에 나오는 순서 그대로 옮긴다. 슬라이드 사이는 빈 줄 하나로 나누고
각 덩이의 첫 줄이 슬라이드 번호다.

장 표지의 눈썹줄만 예외로 뺀다. 그 줄은 장 번호 숫자 하나뿐이라 바로 위의 슬라이드
번호와 숫자 두 줄이 잇달아 붙는다. 제목이 장 이름을 그대로 말해 주므로 잃는 것이 없다.

    python _export_text.py

차트는 role="img"로 묶여 있어 화면 낭독기가 안쪽 숫자를 낱개로 읽지 않는다. 그래서
여기서도 안쪽 대신 그 카드에 붙은 설명문(sr-only) 한 줄만 가져온다. 화면에서 듣는 것과
텍스트로 읽는 것을 같게 두려는 것이다.
"""
import sys
from html.parser import HTMLParser
from pathlib import Path

VOID = {"br", "img", "hr", "meta", "link", "input", "source", "col", "area", "base"}
BLOCK = {"p", "li", "h1", "h2", "h3", "figcaption"}

OUT_NAME = "발표용 텍스트.txt"
TARGETS = [
    Path(__file__).parent,
    Path(r"G:\내 드라이브\KHY\Lectures\260814 국립생물자원관 교육강사 워크숍"),
]


class SlideText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slides = []
        self.lines = None
        self.depth = 0
        self.slide_depth = None
        self.img_depth = None
        self.buf = None
        self.keep = True
        self.eyebrow = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "").split()
        if tag not in VOID:
            self.depth += 1

        if self.slide_depth is None:
            if tag == "div" and "slide" in cls:
                self.slide_depth = self.depth
                self.lines = []
            return

        if tag == "br":
            # 화면에서는 한 문장을 두 줄로 앉힌 자리다. 읽을 때는 한 줄이 낫다.
            if self.buf is not None:
                self.buf.append(" ")
            return

        if a.get("role") == "img" and self.img_depth is None:
            self.img_depth = self.depth

        if tag in BLOCK and self.buf is None:
            self.buf = []
            self.eyebrow = "eyebrow" in cls
            # 차트 안에서는 카드 전체를 대신하는 설명문 한 줄만 가져온다.
            self.keep = "sr-only" in cls if self.img_depth is not None else True

    def handle_endtag(self, tag):
        if self.slide_depth is not None and tag in BLOCK and self.buf is not None:
            text = "".join(self.buf)
            for line in text.split("\n"):
                line = " ".join(line.split())
                if not line or not self.keep:
                    continue
                # 장 표지의 눈썹줄은 장 번호 숫자 하나다. 텍스트에서는 바로 위의
                # 슬라이드 번호와 숫자 두 줄이 잇달아 붙어 어느 쪽인지 헷갈린다.
                # 제목이 장 이름을 그대로 말해 주므로 이 줄만 뺀다.
                if self.eyebrow and line.isdigit():
                    continue
                self.lines.append(line)
            self.buf = None
            self.keep = True
            self.eyebrow = False

        if tag not in VOID:
            if self.img_depth is not None and self.depth == self.img_depth:
                self.img_depth = None
            if self.slide_depth is not None and self.depth == self.slide_depth:
                self.slides.append(self.lines)
                self.lines = None
                self.slide_depth = None
            self.depth -= 1

    def handle_data(self, data):
        if self.buf is not None:
            self.buf.append(data)


def main():
    html = Path(__file__).parent / "index.html"
    p = SlideText()
    p.feed(html.read_text(encoding="utf-8"))

    blocks = []
    for i, lines in enumerate(p.slides, 1):
        blocks.append("\n".join([str(i)] + lines))
    text = "\n\n".join(blocks) + "\n"

    for d in TARGETS:
        if not d.is_dir():
            print(f"[건너뜀] 폴더가 없다: {d}")
            continue
        out = d / OUT_NAME
        # 점자정보단말기와 윈도 편집기를 함께 고려해 CRLF로 쓴다.
        out.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        print(f"{out} · {len(p.slides)}장 · {len(text.splitlines())}줄")
    return 0


if __name__ == "__main__":
    sys.exit(main())
