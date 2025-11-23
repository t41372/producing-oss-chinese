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
    # 审查章节: `{chapter}.xml`

    请对下面的中文翻译进行深度的审查。下面的中文版本是 AI 翻译出来的，请深度对比英文原文，对翻译成果进行批判性审查，撰写一份审查报告和改进措施。

    审查报告指出问题时，要明确写出有问题的位置，推荐引用有问题的原文。

    特别注意下面几个问题
    - 语序和句子结构问题: 作为成熟的翻译者，我们需要对句子结构进行改动 (必要时彻底重组句子)，让句子更符合中文的使用习惯，使文章读起来更通顺。这是审查时需要着重关注的方向。
    - 去掉翻译腔和读起来生硬的句子和用词。
    - 关注错翻，漏翻等关键问题。
    - 英文人名，地名，组织名 或是一些最好附带英文原文来帮助理解的重要概念，旁边应该附带 `(英文原文)`，比如 "加州大学伯克利分校 (University of California at Berkerley)"。不过仅限于那些有必要提供英文的状况。过于 trivial 的就不用了，免得读者觉得我们故意用中英混杂来装逼。
    - 缺字漏字，破碎语法，笔误。
    - 深度评估译文的用词选词是否准确传达了原文的意思，是否符合中文的表达习惯。

    在审查报告中，使用句引用 + 修改案例的方式指出问题，并批量列出同一问题在翻译文本中所有其他状况。修改者是懒散的，你如果不提，他就绝对不会改，所以一定得把需要修改的地方说完整。

    你的报告中应该指出所有问题并给出修改案例。不要提供大段大段的完整新版本翻译。你的任务是给出审查报告和修改建议，而非帮修改者进行修改。

    你写的报告会与其他章节的审查报告在汇总后直接发送给修改者进行修改。

    ⚠️ 若发现中英文对照明显错位或内容不对应，请在审查报告开头先警告“审核材料疑似错位”，再继续指出具体问题。
    
    ## 中文翻译 - 译者指南
    ~~~markdown
    你将作为译者，参与翻译 Karl Fogel 的著作 **《Producing Open Source Software》**（暂译：《生产开源软件》）。

    你的目标翻译语言是：**2025 年的简体中文**。

    # **1. 导言：本书的目的与读者**

    从本质上说，**《Producing Open Source Software》是一本关于“人”的实操手册**。它不只谈代码，更强调如何高效地组织和运营一个志愿者社区，让一个自由软件项目得以诞生、运转、成长。

    * **核心目标：** 提供经过验证的建议与可落地的方法，帮助你把一个开源项目“跑起来、跑稳、跑久”。
    * **面向读者：** 软件开发者、项目经理，以及任何想发起或参与开源项目的人。默认你具备一定技术背景，但本书更关注**社会结构、沟通协作与项目治理**。

    翻译时请体现以上定位：语言**清晰、务实、鼓励**，让读者读完就能去带项目、能带好项目。

    ---

    # **2. 核心概念与开源文化**

    想把本书翻译到位，必须先吃透开源的文化语境。考虑到可能会有多位译者分工协作，统一的上下文尤为关键。

    * **Free Software vs. Open Source：** 二者常被混用，但 Karl Fogel 说话很精准。**“Free software（自由软件）”**（由 Richard Stallman 倡导）强调用户自由：自由运行、复制、传播、研究、修改与改进软件。**“Open source（开源）”**则更偏重工程与协作层面的务实价值，如可靠性与协作效率。全书会交替使用两者，且往往是有意为之——翻译时尽量**保留这种细微差别**。
    * **“开明独裁者”（Benevolent Dictator）：** 常见的治理模型：由一位项目领袖拥有最终拍板权。这并非“独裁”的负面含义，而是为了**高效决策与冲突收敛**。翻译时要把“benevolent（善意/开明）”的意味传达出来。
    * **Meritocracy（精英治/任人唯贤）：** 在开源里，影响力来自**贡献与能力**，不是头衔或年资。好点子可以来自任何人；看重的是**你做了什么**，而不是你是谁。
    * **透明至上：** 几乎所有沟通（讨论、决策、缺陷报告）都在公共空间进行，如邮件列表、Issue/PR。公开透明建立信任，也形成可追溯的集体记忆。
    * **“早发布、勤发布”（Release Early, Release Often）：** Eric S. Raymond 的口号。尽早把代码抛给社区、频繁迭代，快速收集反馈与缺陷报告。
    * **Fork（派生/分叉）：** 从项目源码复制一份，独立开展开发。Fork 是开源的**基本权利**，也是对项目管理者权力的一种**制衡**。

    ---

    # **3. 全书结构概览**

    本书按一个项目的生命周期推进。理解全貌有助于把你所译章节放回正确的位置上。

    * **Part I：从零开始（Getting Started）**
    选许可证、取名、搭建基础设施（版本控制、网站、缺陷跟踪）。
    * **Part II：技术侧（The Technical Side）**
    讲工具与流程：版本控制（以 Subversion 为例，但概念同样适用于 Git）、缺陷管理、自动化测试等。
    * **Part III：人的管理（Managing People）** ★**重点**
    如何带志愿者、搭沟通机制、应对“有毒行为”（poisonous people）、成长社区。
    * **Part IV：钱、法律与商业（Money, Law, and Business）**
    资金、版权与商标、如何与公司打交道等“非技术但很关键”的议题。

    比如你在翻译第三部分的某章，要默认读者已经在第二部分完成了基础技术铺设。

    ---

    # **4. 作者笔触与风格**

    Karl Fogel 的写作风格是这本书的“味道”。翻译时请尽量对齐：

    * **权威但不端着：** 来自一线经验，但不居高临下。更像是“这是我们试过有效的做法”，而不是“金科玉律”。
    * **实操直给：** 语言直接、可执行，避免学究腔/公文腔/企业黑话。中文可以适当“口语化”，但**不过界**。
    * **鼓励与共情：** 作者理解带志愿者项目的难处，像一位资深前辈在旁边出点子、打气、帮踩坑。
    * **略带随和与比喻：** 适度类比与幽默可让观点更易懂。可用中文语境下自然的表达，但**不要硬造梗**。

    ---

    # **5. 翻译规范：术语与排版**

    多人协作时，**一致性最重要**。请严格遵循下面规则。

    ## **术语（Terminology）**

    强烈建议维护一份**共享的在线术语表**，由项目维护者统一管理。初始规范如下：

    * **技术行话尽量不翻：** 属于全球开发者“共通词汇”的术语，保留英文，避免误解。

    * **示例：** `commit`、`fork`、`repository`/`repo`、`pull request`、`branch`、`merge`、`bug`、`patch`、`release`、`API`
    * **判断法则：** **终端里会敲的命令**（如 `git commit`）**一律不翻**。
    * **软件与项目名：** 保留原文（如 `Subversion`、`Apache`、`Linux`、`GNU`）。
    * **首字母缩略词（Acronyms）：** 首次出现请给出**中文全称 + 英文缩写**，后续可直接用缩写。

    * **示例：** 常见问题（FAQ）、自由及开源软件（FOSS）。
    * **代码与链接：** 代码块、内联代码、URL **一律原样保留**，不做翻译与改写。

    ## **排版（Formatting）**

    * **等宽体（Monospaced）：** 命令、文件名、代码请使用等宽体标记，保持原书格式。
    * **斜体与粗体：** 原文哪里使用强调（斜体/粗体），中文对应保留。

    ## **文化与语感（Cultural Nuances）**

    * **成语与比喻：** 英文里偶有只在英语文化成立的表达，**不要直译**。用**功能等效**的中文说法。

    * **示例：** “not rocket science” 可译为“并不复杂”“称不上什么高难度活儿”，而非“不是火箭科学”。

    感谢你的投入与打磨。你正在帮助这本重要资源触达更多读者，也在为全球无数软件项目的成功添一把力。🌎✨

    你的目标翻译语言是：**2025 年的简体中文**。可以适度借用当下中文互联网（知乎/小红书/哔哩哔哩/微信/抖音/快手）的表达，但别太口语化，也别虚头巴脑；**请遵循原文情绪与力度**。

    ~~~

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
