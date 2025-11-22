"""Generate bilingual review packets with structural alignment and ~32k-token chunks.

For each `chXX.xml` pair under `book/en` and `book/zh`, create one or more
Markdown files in `review/` that embed the review prompt and a block-by-block
English/Chinese aligned XML stream.

The alignment logic is structural:
1. It traverses the XML tree recursively.
2. It aligns "Container" elements (sections, lists) by structure.
3. It aligns "Content" elements (paragraphs) by grouping them between "Anchors" (titles, screens).
4. If content counts mismatch within a group, it emits a single N:M pair rather than failing.

Run: `python3 scripts/generate_review_materials.py`
"""

from itertools import zip_longest
from pathlib import Path
from textwrap import dedent
import html
from lxml import etree as ET
from copy import deepcopy
import tiktoken
import difflib


ROOT = Path(__file__).resolve().parent.parent
EN_DIR = ROOT / "book" / "en"
ZH_DIR = ROOT / "book" / "zh"
REVIEW_DIR = ROOT / "reviews"

# Soft target token budget per review file; pairs are never split. Oversized
# single pairs may exceed this target but stay intact.
TARGET_TOKEN = 32_000


# Tags we recurse into (Containers)
RECURSIVE_TAGS = {
    "book",
    "part",
    "chapter",
    "preface",
    "dedication",
    "colophon",
    "appendix",
    "bibliography",
    "glossary",
    "index",
    "setindex",
    "reference",
    "refentry",
    "sect1",
    "sect2",
    "sect3",
    "sect4",
    "sect5",
    "section",
    "simplesect",
    "article",
    "sidebar",
    "blockquote",
    "note",
    "tip",
    "warning",
    "caution",
    "important",
    "itemizedlist",
    "orderedlist",
    "variablelist",
    "procedure",
    "task",
    "qandaset",
    "qandaentry",
    "question",
    "answer",
    "listitem",
    "step",
    "varlistentry",
    "calloutlist",
    "callout",
    "footnote",
}

# Tags we treat as atomic anchors (Leaf Anchors)
ANCHOR_TAGS = {
    "programlisting",
    "screen",
    "literallayout",
    "screenshot",
    "graphic",
    "mediaobject",
    "table",
    "informaltable",
    "figure",
    "example",
    "title",
    "bridgehead",
    "remark",
}

# All other tags are treated as "Soft Content" (e.g. para, simpara, term)


TEMPLATE = dedent(
    """
    审查章节: `{chapter}.xml`

    请对下面的中文翻译进行深度的审查。下面的中文版本是 AI 翻译出来的，请深度对比英文原文，对翻译成果进行批判性审查，撰写一份审查报告和改进措施。

    审查报告指出问题时，要明确写出有问题的位置，推荐引用有问题的原文。

    特别注意下面几个问题
    - 语序和句子结构问题: 作为成熟的翻译者，我们需要对句子结构进行改动 (必要时彻底重组句子)，让句子更符合中文的使用习惯，使文章读起来更通顺。这是审查时需要着重关注的方向。
    - 去掉翻译腔和读起来生硬的句子和用词。
    - 关注错翻，漏翻等关键问题。
    - 英文人名，地名，组织名 或是一些最好附带英文原文来帮助理解的重要概念，旁边应该附带 `(英文原文)`，比如 "加州大学伯克利分校 (University of California at Berkerley)"。不过仅限于那些有必要提供英文的状况。过于 trivial 的就不用了，免得读者觉得我们故意用中英混杂来装逼。
    - 缺字漏字，破碎语法，笔误。

    在审查报告中，使用句引用 + 修改案例的方式指出问题，并批量列出同一问题在翻译文本中所有其他状况。修改者是懒散的，你如果不提，他就绝对不会改，所以一定得把需要修改的地方说完整。

    你的报告中应该指出所有问题并给出修改案例。不要提供大段大段的完整新版本翻译。你的任务是给出审查报告和修改建议，而非帮修改者进行修改。

    你写的报告会与其他章节的审查报告在汇总后直接发送给修改者进行修改。

    ⚠️ 若发现中英文对照明显错位或内容不对应，请在审查报告开头先警告“审核材料疑似错位”，再继续指出具体问题。

    # 审核文本 (中英对照)
    下面是原文英文文本和中文翻译(被审核文本)的逐段对照文本。最终的翻译是两个分开的档案，不过这里方便你审核，做了合并。

    ==============

    {bilingual}

    ==============
    """
).strip()


def local_name(tag: str) -> str:
    """Drop namespaces for comparison and labeling."""
    if not isinstance(tag, str):
        return ""
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def element_to_string(elem: ET._Element) -> str:
    """Serialize a block."""
    return ET.tostring(elem, encoding="unicode")


def estimate_tokens(text: str, enc) -> int:
    """Token count using tiktoken; shared encoder passed in for speed."""
    return len(enc.encode(text, disallowed_special=()))


def load_xml(path: Path) -> ET._Element:
    # Resolve common HTML entities (&nbsp; &mdash;, etc.) used in source files
    # manually to avoid unescaping XML structure chars like &lt; or &gt;.
    text = path.read_text(encoding="utf-8")

    # Replace known HTML entities with numeric character references
    replacements = {
        "&nbsp;": "&#160;",
        "&mdash;": "&#8212;",
        "&ldquo;": "&#8220;",
        "&rdquo;": "&#8221;",
        "&lsquo;": "&#8216;",
        "&rsquo;": "&#8217;",
        "&copy;": "&#169;",
        "&reg;": "&#174;",
        "&trade;": "&#8482;",
        "&hellip;": "&#8230;",
    }
    for entity, char_ref in replacements.items():
        text = text.replace(entity, char_ref)

    parser = ET.XMLParser(resolve_entities=False, recover=True)
    return ET.fromstring(text.encode("utf-8"), parser)


def get_chunk_type(elem: ET._Element) -> str:
    tag = local_name(elem.tag)
    if tag in RECURSIVE_TAGS:
        return f"RECURSIVE:{tag}"
    elif tag in ANCHOR_TAGS:
        return f"ANCHOR:{tag}"
    else:
        return "SOFT"


def group_children(parent: ET._Element) -> list[tuple[str, list[ET._Element]]]:
    """Group children into chunks of (Type, [Elements]).

    Types are:
    - RECURSIVE:{tag} (Single element)
    - ANCHOR:{tag} (Single element)
    - SOFT (List of contiguous soft elements)
    """
    chunks = []
    current_soft = []

    for child in parent:
        if not isinstance(child.tag, str):
            continue

        ctype = get_chunk_type(child)

        if ctype == "SOFT":
            current_soft.append(child)
        else:
            if current_soft:
                chunks.append(("SOFT", current_soft))
                current_soft = []
            chunks.append((ctype, [child]))

    if current_soft:
        chunks.append(("SOFT", current_soft))

    return chunks


def recursive_pair(en_elem: ET._Element, zh_elem: ET._Element) -> list[str]:
    """Recursively align EN and ZH elements and return list of review blocks."""

    results = []

    # Group children into alignable chunks
    en_chunks = group_children(en_elem)
    zh_chunks = group_children(zh_elem)

    en_types = [c[0] for c in en_chunks]
    zh_types = [c[0] for c in zh_chunks]

    matcher = difflib.SequenceMatcher(None, en_types, zh_types)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            # 1:1 match of chunk types
            for k in range(i2 - i1):
                en_type, en_items = en_chunks[i1 + k]
                zh_type, zh_items = zh_chunks[j1 + k]

                if en_type.startswith("RECURSIVE:"):
                    # Recurse into container
                    # en_items and zh_items have exactly 1 element each
                    results.extend(recursive_pair(en_items[0], zh_items[0]))

                elif en_type.startswith("ANCHOR:"):
                    # Atomic anchor, emit pair
                    en_xml = element_to_string(en_items[0])
                    zh_xml = element_to_string(zh_items[0])
                    results.append(format_pair(en_xml, zh_xml))

                else:  # SOFT
                    # Soft sequence match.
                    # If counts match, emit 1:1 pairs (optional, but nice)
                    # If counts mismatch, emit N:M pair
                    if len(en_items) == len(zh_items):
                        for em, zm in zip(en_items, zh_items):
                            results.append(
                                format_pair(
                                    element_to_string(em), element_to_string(zm)
                                )
                            )
                    else:
                        # Mismatch in soft content count, emit block
                        en_xml = "\n".join(element_to_string(x) for x in en_items)
                        zh_xml = "\n".join(element_to_string(x) for x in zh_items)
                        results.append(format_pair(en_xml, zh_xml))

        else:
            # Mismatch (replace, delete, insert)
            # Merge all chunks in the range
            en_range_items = []
            for k in range(i1, i2):
                en_range_items.extend(en_chunks[k][1])

            zh_range_items = []
            for k in range(j1, j2):
                zh_range_items.extend(zh_chunks[k][1])

            en_xml = (
                "\n".join(element_to_string(x) for x in en_range_items)
                if en_range_items
                else "(MISSING)"
            )
            zh_xml = (
                "\n".join(element_to_string(x) for x in zh_range_items)
                if zh_range_items
                else "(MISSING)"
            )

            results.append(format_pair(en_xml, zh_xml))

    return results


def format_pair(en_xml: str, zh_xml: str) -> str:
    return (
        "英文原文\n"
        "```xml\n"
        f"{en_xml.strip()}\n"
        "```\n"
        "中文翻译\n"
        "```xml\n"
        f"{zh_xml.strip()}\n"
        "```"
    )


def build_bilingual(en_root: ET._Element, zh_root: ET._Element) -> list[str]:
    return recursive_pair(en_root, zh_root)


def flatten_para(elem: ET._Element) -> None:
    parent = elem.getparent()
    if parent is None:
        return

    # Check if needs flattening
    has_block = False
    for child in elem:
        if local_name(child.tag) in RECURSIVE_TAGS:
            has_block = True
            break

    if not has_block:
        return

    index = parent.index(elem)
    new_elements = []

    # Initial text
    if elem.text and elem.text.strip():
        p = ET.Element(elem.tag)
        p.text = elem.text
        for k, v in elem.items():
            p.set(k, v)
        new_elements.append(p)

    for child in elem:
        is_block = local_name(child.tag) in RECURSIVE_TAGS

        if is_block:
            # Handle the block element
            tail = child.tail
            child.tail = None
            new_elements.append(child)

            # If there is tail text, start a new para
            if tail and tail.strip():
                p = ET.Element(elem.tag)
                p.text = tail
                for k, v in elem.items():
                    p.set(k, v)
                new_elements.append(p)
        else:
            # Inline element
            if not new_elements or local_name(new_elements[-1].tag) != local_name(
                elem.tag
            ):
                p = ET.Element(elem.tag)
                for k, v in elem.items():
                    p.set(k, v)
                new_elements.append(p)

            new_elements[-1].append(child)

    # Handle original tail of the para being replaced
    if elem.tail:
        if new_elements:
            if new_elements[-1].tail:
                new_elements[-1].tail += elem.tail
            else:
                new_elements[-1].tail = elem.tail

    parent.remove(elem)
    for i, new_el in enumerate(new_elements):
        parent.insert(index + i, new_el)


def preprocess_xml(root: ET._Element) -> None:
    """Flatten block elements inside paragraphs to simplify alignment."""
    # Iterate over a list of elements to avoid modification issues during iteration
    for elem in list(root.iter()):
        if local_name(elem.tag) == "para":
            flatten_para(elem)


def generate_review_file(en_path: Path) -> None:
    chapter = en_path.stem  # e.g., ch03
    zh_path = ZH_DIR / f"{chapter}.xml"
    if not zh_path.exists():
        raise FileNotFoundError(f"Missing Chinese file for {chapter}: {zh_path}")

    en_root = load_xml(en_path)
    zh_root = load_xml(zh_path)

    preprocess_xml(en_root)
    preprocess_xml(zh_root)

    # Clean old outputs up front to avoid stale files on failures.
    for old in REVIEW_DIR.glob(f"{chapter}*-review.md"):
        old.unlink(missing_ok=True)

    try:
        bilingual_blocks = build_bilingual(en_root, zh_root)
    except ValueError as exc:
        print(f"[ERROR] {en_path.name}: {exc}")
        return

    enc = tiktoken.get_encoding("cl100k_base")

    # Split into size-limited chunks using token estimates, never splitting a pair.
    template_overhead = estimate_tokens(
        TEMPLATE.format(chapter=chapter, bilingual=""), enc
    )
    sep_tokens = estimate_tokens("\n\n---\n\n", enc)

    chunks: list[list[str]] = []
    current: list[str] = []
    current_tokens = template_overhead

    for block_text in bilingual_blocks:
        block_tokens = estimate_tokens(block_text, enc)
        # If adding this pair would exceed target, start new chunk first.
        if current and current_tokens + sep_tokens + block_tokens > TARGET_TOKEN:
            chunks.append(current)
            current = []
            current_tokens = template_overhead
        if current:
            current_tokens += sep_tokens
        current.append(block_text)
        current_tokens += block_tokens

    if current:
        chunks.append(current)

    # Emit one file or multiple with numeric suffixes.
    if len(chunks) == 1:
        out_path = REVIEW_DIR / f"{chapter}-review.md"
        bilingual_body = "\n\n---\n\n".join(chunks[0])
        out_path.write_text(
            TEMPLATE.format(chapter=chapter, bilingual=bilingual_body),
            encoding="utf-8",
        )
        return
    else:
        for idx, chunk_blocks in enumerate(chunks, start=1):
            out_path = REVIEW_DIR / f"{chapter}-{idx}-review.md"
            bilingual_body = "\n\n---\n\n".join(chunk_blocks)
            out_path.write_text(
                TEMPLATE.format(chapter=chapter, bilingual=bilingual_body),
                encoding="utf-8",
            )
        return


def main() -> None:
    REVIEW_DIR.mkdir(exist_ok=True)

    chapters = sorted(EN_DIR.glob("ch??.xml"))
    if not chapters:
        raise SystemExit("No chapter files found under book/en")

    success = 0
    for en_path in chapters:
        generate_review_file(en_path)
        if any(REVIEW_DIR.glob(f"{en_path.stem}*-review.md")):
            success += 1

    print(
        f"Generated review files for {success}/{len(chapters)} chapters in {REVIEW_DIR}"
    )


if __name__ == "__main__":
    main()
