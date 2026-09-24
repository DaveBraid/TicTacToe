"""下载系列文章正文与图片，生成可离线阅读的 HTML。"""

import hashlib
import html
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ARTICLES = [
    ('01', '自定义 Gym 环境', 'https://www.cnblogs.com/wsy950409/p/15645049.html'),
    ('02', '井字棋环境', 'https://www.cnblogs.com/wsy950409/p/15647914.html'),
    ('03', 'Q 表框架', 'https://www.cnblogs.com/wsy950409/p/15658371.html'),
    ('04', '开始训练', 'https://www.cnblogs.com/wsy950409/p/15665291.html'),
    ('05', '优化训练', 'https://www.cnblogs.com/wsy950409/p/15673376.html'),
    ('06', '游戏时间', 'https://www.cnblogs.com/wsy950409/p/15680697.html'),
]
ROOT = Path(__file__).resolve().parents[1] / 'handbooks'
NAV_STYLE = '''
.chapter-nav{display:flex;justify-content:space-between;gap:1rem;margin:2rem 0 1rem}
.chapter-nav a{display:inline-block;padding:.65rem 1rem;border:1px solid #ccd6e0;border-radius:.5rem;background:#f4f8fc;color:#174a76;text-decoration:none}
.chapter-nav a:hover,.chapter-nav a:focus-visible{background:#e5f1fb;border-color:#77a8d3}
.chapter-nav .next{margin-left:auto;text-align:right}
'''


def navigation(number):
    '''生成文章底部的上一篇和下一篇按钮。

    思路：从固定阅读顺序中寻找相邻文章；首尾连接学习目录。
    输入：当前文章编号。输出：两侧链接的 HTML。
    '''
    index = next(i for i, article in enumerate(ARTICLES) if article[0] == number)
    previous = ARTICLES[index - 1] if index > 0 else None
    following = ARTICLES[index + 1] if index + 1 < len(ARTICLES) else None
    prev_href = f'{previous[0]}-原文备份.html' if previous else 'README.md'
    next_href = f'{following[0]}-原文备份.html' if following else 'README.md'
    prev_label = f'上一篇：{previous[1]}' if previous else '返回学习目录'
    next_label = f'下一篇：{following[1]}' if following else '返回学习目录'
    return (f'<nav class="chapter-nav" aria-label="文章导航">'
            f'<a class="previous" href="{prev_href}">← {html.escape(prev_label)}</a>'
            f'<a class="next" href="{next_href}">{html.escape(next_label)} →</a></nav>')


class BodyLocator(HTMLParser):
    '''定位博客正文在原始 HTML 中的边界。

    思路：按 div 嵌套深度匹配 cnblogs_post_body 的结束标签。
    输入：整页 HTML。输出：start/end 字符偏移量。
    '''

    def __init__(self, page):
        super().__init__(convert_charrefs=False)
        self.page = page
        self.line_starts = [0] + [m.end() for m in re.finditer('\n', page)]
        self.start = None
        self.end = None
        self.depth = 0
        self.feed(page)

    def char_offset(self):
        '''将解析器位置转换为字符偏移。

        思路：累计前面各行字符数后加上当前列数。
        输入：解析器当前行列。输出：字符偏移。
        '''
        row, col = self.getpos()
        return self.line_starts[row - 1] + col

    def handle_starttag(self, tag, attrs):
        '''记录目标正文起点和 div 深度。

        思路：找到目标 id 后，对内部 div 计数。
        输入：标签及属性。输出：无。
        '''
        if tag != 'div':
            return
        if self.start is None and dict(attrs).get('id') == 'cnblogs_post_body':
            self.start = self.char_offset() + len(self.get_starttag_text())
            self.depth = 1
        elif self.depth:
            self.depth += 1

    def handle_endtag(self, tag):
        '''记录目标正文结束位置。

        思路：目标 div 的嵌套深度回到零时保存偏移。
        输入：结束标签名。输出：无。
        '''
        if tag == 'div' and self.depth:
            self.depth -= 1
            if self.depth == 0:
                self.end = self.char_offset()


def download(url, referer=None):
    '''下载网页或图片内容。

    思路：指定浏览器标识和原文来源，超时后抛错以避免不完整备份。
    输入：资源网址、可选来源网址。输出：响应字节。
    '''
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; offline-archive/1.0)'}
    if referer:
        headers['Referer'] = referer
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return response.read()


def backup_one(number, title, url):
    '''保存一篇文章正文及正文中的图片。

    思路：截取正文，图片改为本地相对路径，再写独立 HTML。
    输入：编号、标题、原文网址。输出：文件与哈希清单。
    '''
    page = download(url).decode('utf-8')
    locator = BodyLocator(page)
    if locator.start is None or locator.end is None:
        raise ValueError(f'未找到文章正文：{url}')
    body = page[locator.start:locator.end]
    assets_dir = ROOT / 'assets' / number
    assets_dir.mkdir(parents=True, exist_ok=True)
    assets = []

    def localize_image(match):
        '''替换一张图片的 src 并保存原文件。

        思路：使用递增编号防止同名图片覆盖，记录来源与校验值。
        输入：img 标签匹配。输出：替换后的标签。
        '''
        tag = match.group(0)
        src_match = re.search(r'\bsrc\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
        if not src_match:
            return tag
        source = urljoin(url, html.unescape(src_match.group(2)))
        if not source.startswith(('https://', 'http://')):
            return tag
        data = download(source, url)
        suffix = Path(urlparse(source).path).suffix.lower()
        if suffix not in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}:
            suffix = '.img'
        name = f'{len(assets) + 1:02d}{suffix}'
        (assets_dir / name).write_bytes(data)
        assets.append({'file': f'assets/{number}/{name}', 'source': source,
                       'sha256': hashlib.sha256(data).hexdigest()})
        return tag[:src_match.start(2)] + f'assets/{number}/{name}' + tag[src_match.end(2):]

    body = re.sub(r'<img\b[^>]*>', localize_image, body, flags=re.I | re.S)
    # 系列文章互相链接时优先打开本地备份。
    for other_number, _, other_url in ARTICLES:
        body = body.replace(other_url, f'{other_number}-原文备份.html')
    output = ROOT / f'{number}-原文备份.html'
    document = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>
body{{max-width:900px;margin:2rem auto;padding:0 1rem;font:16px/1.7 system-ui,sans-serif;color:#222}}
img{{max-width:100%;height:auto}} pre{{overflow:auto;padding:1rem;background:#f5f5f5}} code{{overflow-wrap:anywhere}}
table{{border-collapse:collapse}}td,th{{border:1px solid #aaa;padding:.35rem}}.source{{border-top:1px solid #ccc;margin-top:3rem}}
{NAV_STYLE}
</style></head><body><h1>{html.escape(title)}</h1>
<p>离线备份于 {date.today().isoformat()} · <a href="{html.escape(url, quote=True)}">原文地址</a> · <a href="README.md">学习路线</a></p>
<main>{body}</main><p class="source">原文作者：埠默笙声声声脉。转载来源：<a href="{html.escape(url, quote=True)}">{html.escape(url)}</a></p>
{navigation(number)}
</body></html>'''
    output.write_text(document, encoding='utf-8')
    print(f'{output.name}: {len(assets)} 张图片')
    return {'file': output.name, 'source': url, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'images': assets}


def main():
    '''批量备份六篇文章并写入来源清单。

    思路：逐篇下载，全部成功后保存可核对的 JSON 清单。
    输入：固定文章列表。输出：HTML、图片和 manifest.json。
    '''
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = [backup_one(*article) for article in ARTICLES]
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
