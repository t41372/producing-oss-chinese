# producing-oss-chinese
Use AI to translate the entire book


原始 svn 仓库
- https://svn.red-bean.com/repos/producingoss/trunk/

原文官网
- https://producingoss.com/

协议: Attribution-ShareAlike 4.0 International

原作者: Karl Fogel


## 这书不是有中文版吗？为什么还要让 AI 翻译

这书的官方中文版翻译的烂到家了，我看到一半就受不了跑去看英文版了。句子翻译的乱七八糟，很多词翻译的也很奇怪，感觉像是早年的 Google 机器翻译。
虽然我没这个精力手动翻译，但我们还有 AI 呀！

AI 翻译很贵，但许多 coding agent，特别是 async coding agent，是按 requests 而非 token 计费的。不管你这个 task 跑了多久，他都只会吃掉一个 request 的额度。

<img width="1717" height="726" alt="截圖 2025-09-03 下午4 36 45" src="https://github.com/user-attachments/assets/0f45512d-133a-4d04-a7df-939f91ae2f2a" />


这对翻译整本书来说就很方便了()

于是就有了这个仓库



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









