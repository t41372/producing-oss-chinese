"""Generate chapter review packets for the second-pass translation audit.

For each `chXX.xml` pair under `book/en` and `book/zh`, emit a Markdown
file at `review/chXX-review.md` that bundles the English source and the
current Chinese translation into the review prompt template supplied by
the editors.

Run: `python scripts/generate_review_materials.py`
"""

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent.parent
EN_DIR = ROOT / "book" / "en"
ZH_DIR = ROOT / "book" / "zh"
REVIEW_DIR = ROOT / "reviews"


TEMPLATE = dedent(
    """
    # 章节审查: `{chapter}`
    
    请对下面的中文翻译进行深度的审查。下面的中文版本是 AI 翻译出来的，请深度对比英文原文，对翻译成果进行批判性审查，撰写一份审查报告和改进措施。

    审查报告指出问题时，要明确写出有问题的位置，推荐引用有问题的原文。

    特别注意下面几个问题
    - 语序和句子结构问题: 作为成熟的翻译者，我们需要对句子结构进行改动 (必要时彻底重组句子)，让句子更符合中文的使用习惯，使文章读起来更通顺。这是审查时需要着重关注的方向。
    - 去掉翻译腔和读起来生硬的句子和用词。
    - 关注错翻，漏翻等关键问题。
    - 英文人名，地名，组织名 或是一些最好附带英文原文来帮助理解的重要概念，旁边应该附带 `(英文原文)`，比如 "加州大学伯克利分校 (University of California at Berkerley)"。不过仅限于那些有必要提供英文的状况。过于 trivial 的就不用了，免得读者觉得我们故意用中英混杂来装逼。

    在审查报告中，使用句引用 + 修改案例的方式指出问题，并批量列出同一问题在翻译文本中所有其他状况。修改者是懒散的，你如果不提，他就绝对不会改，所以一定得把需要修改的地方说完整。

    你的报告中应该指出所有问题并给出修改案例。不要提供大段大段的完整新版本翻译。你的任务是给出审查报告和修改建议，而非帮修改者进行修改。
    
    你写的报告会与其他章节的审查报告在汇总后直接发送给修改者进行修改。

    # 英文原版
    ```xml
    {english}
    ```

    # 中文翻译

    ```xml
    {chinese}
    ```
    """
).strip()


def generate_review_file(en_path: Path) -> None:
    chapter = en_path.stem  # e.g., ch03
    zh_path = ZH_DIR / f"{chapter}.xml"
    if not zh_path.exists():
        raise FileNotFoundError(f"Missing Chinese file for {chapter}: {zh_path}")

    english = en_path.read_text(encoding="utf-8")
    chinese = zh_path.read_text(encoding="utf-8")

    review_text = TEMPLATE.format(english=english, chinese=chinese, chapter=chapter)

    out_path = REVIEW_DIR / f"{chapter}-review.md"
    out_path.write_text(review_text, encoding="utf-8")


def main() -> None:
    REVIEW_DIR.mkdir(exist_ok=True)

    chapters = sorted(EN_DIR.glob("ch??.xml"))
    if not chapters:
        raise SystemExit("No chapter files found under book/en")

    for en_path in chapters:
        generate_review_file(en_path)

    print(f"Generated {len(chapters)} review files in {REVIEW_DIR}")


if __name__ == "__main__":
    main()
