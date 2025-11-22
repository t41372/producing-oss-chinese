# producing-oss-chinese
> This repository is an attempt to translate the book "[Producing Open Source Software](https://producingoss.com/)" by [Karl Fogel](http://www.red-bean.com/kfogel/) into Chinese with LLMs. The rest of the docs will be written in Chinese.

## Introduction
The goal of this repository is to translate the book "[Producing Open Source Software](https://producingoss.com/)" by [Karl Fogel](http://www.red-bean.com/kfogel/) into Chinese with LLMs.

The reason to do this despite the existence of an official translation is because the official Chinese translation is a hot trash. That translation is so bad, calling it 'pre-LLM machine translation' would be an insult to machine translation. I was on a flight when I read that book, and I was so furious that I figured reading the English version would be much faster than demystifying the Chinese translation like climbing up the babel tower (I'm a chinese native speaker). The garbage translation feel so pathetic, because we are at the age where the Chinese open source community is rising. A new generation of developers are growing up. This book is pure gold, but the translation is pure garbage. I decided to fix it.

I'm no where near a good translator. If I were to translate the book myself, it would merely be a bit better than the original version and still far from acceptable. I decided to use a combination of LLMs to translate the book.

LLMs are not perfect. Actually, they are quite bad. I used some guardrails like linters and LLM code review from Gemini 2.5, GPT-5-High, and Claude 4.5 Sonnet with extended thinking to mitigate problems, but errors can still occur. Please feel free to open issues whenever you encounter errors.

这个仓库的目的是使用 AI，将 Karl Fogel 的 生产开源软件 一书翻译成中文。



<img width="145" height="190" alt="image" src="https://github.com/user-attachments/assets/8467c206-4d2e-4811-9e8a-0bb06a732eff" />


这本书翻译时，我们 (我和 AI) 的假设是你至少看得懂一些英文，因此我们会保留人名和许多术语的英文原文，这对程序员来说可能比奇怪的翻译更熟悉。我认为这本书的目标受众是看得懂英文的 - 甚至能看得懂英文原版，只是读原文书太累。



原始 svn 仓库
- https://svn.red-bean.com/repos/producingoss/trunk/

原文官网
- https://producingoss.com/

协议: Attribution-ShareAlike 4.0 International

原作者: Karl Fogel


## 构建指南

翻译内容完成后，可以借助项目内置的 Docker 化工具链把整本书打包为 HTML、EPUB 与 PDF。整个流程不会在宿主机上安装 DocBook/FOP，只需要 Docker。

如果你更希望直接使用本机已经安装好的 DocBook/FOP 工具链，也可以运行新的 `scripts/build-book-local.sh`，完全跳过 Docker（见下文“本地工具链”）。

### 快速开始

1. 确保本机已安装并启动 Docker Desktop（或其他兼容的 Docker 守护进程）。
2. 在仓库根目录执行：

   ```bash
   ./scripts/build-book.sh zh
   ```

   脚本会：
   - 根据 `docker/builder.Dockerfile` 构建一个包含 `xsltproc`、DocBook XSL、Apache FOP、fonts-noto-cjk 等依赖的容器镜像；
   - 在容器里自动下载官方 `tools/`、`lang-makefile`、`styles.css`；
   - 用当前 Git 提交信息生成 `book/zh/book.xml`；
   - 依次运行 `html html-chunk epub pdf` 四个 `make` 目标，产出 `book/zh/producingoss.html`、`book/zh/html-chunk/`、`book/zh/producingoss.epub` 与各纸张尺寸的 PDF。

### 本地工具链（不使用 Docker）

如果不使用 docker，请确保环境中已经安装相关依赖:
```sh
sudo apt-get update && sudo apt-get install -y make subversion xsltproc docbook-xsl docbook-xsl-ns fop default-jre-headless zip libxml2-utils
```

若你的环境里已经安装好 DocBook/FOP 相关依赖，可以直接运行：

```bash
./scripts/build-book-local.sh zh
```

该脚本会重用 `scripts/internal/build-inside-container.sh`，步骤与 Docker 版完全一致，但所有命令都在宿主机执行。请先准备好以下工具（名称以 Debian/Ubuntu 软件包为例）：

- `make`
- `svn`
- `xsltproc` 与 `docbook-xsl`/`docbook-xsl-ns`
- `fop`（包含 `default-jre-headless`）
- `zip`、以及 `libxml2-utils`

如果只想生成某些格式，可以和 Docker 方案一样通过 `BUILD_TARGETS` 环境变量覆盖默认值；`POSS_SVN_BASE`、`FOP_OPTS`、`HTML_CHUNK_DIR_OVERRIDE` 等变量同样受支持。

### 可选参数

- 切换语言：`./scripts/build-book.sh en zh` 会顺序构建 `book/en` 与 `book/zh`。
- 覆盖构建目标：`BUILD_TARGETS="html epub" ./scripts/build-book.sh zh`。
- 自定义镜像标签或 Dockerfile：通过 `POSS_BUILDER_IMAGE`、`POSS_DOCKERFILE` 环境变量控制。

### GitHub Actions 自动构建

`.github/workflows/build-book.yml` 会在相关文件变更或手动触发时运行同一套脚本，并把生成的 HTML/EPUB/PDF 作为构建工件（artifact）上传，方便下载或后续部署。

### 构建产物位置

所有生成文件位于 `book/<语言代码>/` 目录下：

- 单页 HTML：`producingoss.html`
- 分片 HTML 目录：`html-chunk/`
- EPUB：`producingoss.epub`
- 多种纸张规格的 PDF：`producingoss-*.pdf`

如需发布到网站，可直接将 `html-chunk/` 与 `producingoss.html` 上传到静态站或 GitHub Pages。


## 协议
翻译版保持原书协议，以 Creative Commons Attribution-ShareAlike License 开源，具体请查看 LICENSE 文件或原书仓库中的协议文件。

### 关于字体
中文版的 pdf 采用[思源黑体 (Source Han Sans) 字体](https://github.com/adobe-fonts/source-han-sans)，该字体以 SIL OPEN FONT LICENSE Version 1.1 开源。

---

## 一些相关的 prompt

一些跟 setup 相关的 prompt 在下面。翻译用的 prompt 在 agents.md 里面。

### context doc prompt
```markdown
We will be deligating the translation work of the book "Producing Open Source Software:

How to Run a Successful Free Software Project" by Karl Fogel into different languages. Please write a detailed translation guide to let the translators know about the context of the entire book (lots of translators will work on discrete pages).
```



### setup prompt

```markdown

下面是 setup 这本书翻译工作的官方指南。
我们不打算用 svn，也不打算推回到原始的仓库了，只打算把档案拿到之后放在我们当前的 git 里面。
我们要翻译的是英翻中，但我们完全不打算使用旧的中文翻译，所以我们应该要先拿到英文的 source，然后再把它翻译成中文。

~~~markdown
Translator guidelines:

These guidelines assume you're familiar with using the Subversion version control system. If you're not, don't worry: we'll find a way to make it easy for you to work on the translation, either by teaching you some Subversion, or by arranging things so that you don't have to use Subversion.

First, get a username and password for repository access by asking here. Then check out a working copy of the relevant translation directory, named after the two-letter standard language code. In this example, it's zh for Chinese:

   $ svn checkout http://svn.red-bean.com/repos/producingoss/trunk/zh/
   $ cd zh
The chapters are named ch00.xml, ch01.xml, etc (and there are a few other XML files, for the table of contents and the appendices). Just edit each file, replacing English text with the target language. (If your software asks you what format to save in, choose "UTF8" or "UTF-8".)

Once you've done enough work and you're ready to save, commit the changes to the repository:

   $ svn commit -m "Translated some more of Chapter 2." ch02.xml
At any time, you can "update" to bring down the changes other people may have made:

   $ svn update
You can use the ViewVC tool here just to check if your work is there or to see the modifications list and differences between them.


~~~

所以我们要怎么做呢？要怎么拿到所有英文的源文件然后开始翻译工作？
顺便帮我规划一下我们这个 git 仓库的 layout。目前我的规划是 root 放一些跟我们翻译工作相关的东西，书的源文件和翻译放在 book 目录下。
```







