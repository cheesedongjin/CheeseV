import os
import re

CONTENT_DIR = 'content'
OUTPUT_DIR = 'docs'
TEMPLATES_DIR = 'templates'
SITE_NAME = 'CheeseV'


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def simple_markdown(md):
    lines = md.splitlines()
    html_lines = []
    in_code_block = False
    code_lang = ''
    list_stack = []
    # 1단계=disc, 2단계=circle, 3단계=none(대시)
    style_map = {1: 'disc', 2: 'circle', 3: 'none'}
    code_lines = []  # To store lines within a code block
    code_indents = []  # To store indentation levels of code lines

    def process_inline(text):
        code_spans = {}
        def repl_code(m):
            key = f"{{{{code{len(code_spans)}}}}}"
            code_content = (
                m.group(1)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            code_spans[key] = f"<code>{code_content}</code>"
            return key
        text = re.sub(r'`([^`]+?)`', repl_code, text)
        # 이미지
        text = re.sub(
            r'!\[([^]]*?)]\((\S+?)(?:\s+"(.*?)")?\)',
            lambda m: (
                f'<img src="{m.group(2)}" alt="{m.group(1)}"'
                + (f' title="{m.group(3)}"' if m.group(3) else '')
                + '>'
            ),
            text
        )
        # 링크: target="_blank" 추가
        text = re.sub(
            r'\[([^]]+?)]\((\S+?)(?:\s+"(.*?)")?\)',
            lambda m: (
                f'<a href="{m.group(2)}" target="_blank"'
                + (f' title="{m.group(3)}"' if m.group(3) else '')
                + f'>{m.group(1)}</a>'
            ),
            text
        )
        # 굵은 글씨
        text = re.sub(r'(\*\*|__)(.+?)\1', r'<strong>\2</strong>', text)
        # 기울임
        text = re.sub(r'([*_])(.+?)\1', r'<em>\2</em>', text)
        # 토큰 복원
        for key, val in code_spans.items():
            text = text.replace(key, val)
        return text

    for line in lines:
        stripped = line.lstrip(' ')
        leading = len(line) - len(stripped)  # Count each space as one indent

        # 코드 블록 펜스 처리 (```lang)
        m_fence = re.match(r'^(\s*)(```)(\w+)?\s*$', line)
        if m_fence:
            indent = len(m_fence.group(1))  # Count spaces for fence indent
            if not in_code_block:
                code_lang = m_fence.group(3) or 'unknown'
                class_attr = f' class="code-block language-{code_lang}"'
                data_attr = f' data-language="{code_lang.upper()}"'
                html_lines.append(
                    f'<div{class_attr}{data_attr} style="margin-left: {indent * 8}px">'
                    f'<button class="copy-button">Copy</button>'
                    f'<pre><code>'
                )
                in_code_block = True
                code_lines = []
                code_indents = []
            else:
                # 코드 블록 종료: 공통 들여쓰기 제거
                if code_lines:
                    min_indent = min(code_indents) if code_indents else 0
                    for code_line in code_lines:
                        if code_line.strip():  # 비어 있지 않은 줄만 처리
                            html_lines.append(code_line[min_indent:])
                        else:
                            html_lines.append(code_line)
                html_lines.append('</code></pre></div>')
                in_code_block = False
                code_lang = ''
                code_lines = []
                code_indents = []
            continue

        if in_code_block:
            # 코드 블록 내부: 줄을 수집하고 들여쓰기 기록
            code_lines.append(line)
            if stripped:  # 비어 있지 않은 줄만 들여쓰기 계산
                code_indents.append(len(line) - len(line.lstrip(' ')))
            continue

        # 헤더
        m_h = re.match(r'^(#{1,6})\s+(.*)', stripped)
        if m_h:
            while list_stack:
                html_lines.append('</ul>')
                list_stack.pop()
            level = len(m_h.group(1))
            content = process_inline(m_h.group(2))
            html_lines.append(f'<h{level}>{content}</h{level}>')
            continue

        # 리스트
        m_list = re.match(r'^([-*])\s+(.*)', stripped)
        if m_list:
            marker, content_raw = m_list.groups()
            content = process_inline(content_raw)
            depth = len(list_stack) + 1 if not list_stack or leading > list_stack[-1] else len(list_stack)
            # 새 리스트 시작
            if not list_stack or leading > list_stack[-1]:
                style = style_map.get(depth, 'disc')
                html_lines.append(
                    f'<ul style="margin-left: {leading*8}px; list-style-type: {style}">'
                )
                list_stack.append(leading)
            else:
                while list_stack and leading < list_stack[-1]:
                    html_lines.append('</ul>')
                    list_stack.pop()
                style = style_map.get(depth, 'disc')
            # 3단계(none)인 경우 항목 앞에 대시 추가
            if style_map.get(depth) == 'none':
                content = '- ' + content
            html_lines.append(f'<li>{content}</li>')
            continue

        # 열린 리스트 닫기
        if list_stack:
            while list_stack:
                html_lines.append('</ul>')
                list_stack.pop()

        # 수평선
        if re.match(r'^-{3,}\s*$', stripped):
            html_lines.append('<hr>')
            continue

        # 단락
        if stripped == '':
            html_lines.append('')
        else:
            indent_html = ' ' * leading
            content = process_inline(stripped)
            html_lines.append(f'<p>{indent_html}{content}</p>')

    # 마무리: 열린 코드 블록 및 리스트 닫기
    if in_code_block:
        if code_lines:
            min_indent = min(code_indents) if code_indents else 0
            for code_line in code_lines:
                if code_line.strip():
                    html_lines.append(code_line[min_indent:])
                else:
                    html_lines.append(code_line)
        html_lines.append('</code></pre></div>')
    if list_stack:
        while list_stack:
            html_lines.append('</ul>')
            list_stack.pop()

    return '\n'.join(html_lines)


def render_template(template_name, **context):
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    template = read_file(template_path)

    # very small template engine using {{ var }} and {% for %}
    result = template
    for key, value in context.items():
        if isinstance(value, str):
            result = result.replace(f"{{{{ {key} }}}}", value)
    pattern = re.compile(r'{% for (\w+) in (\w+) %}(.*?){% endfor %}', re.S)
    while True:
        m = pattern.search(result)
        if m:
            var_name, list_name, body = m.groups()
            items = context.get(list_name, [])
            rendered = ''
            for item in items:
                temp = body
                for k, v in item.items():
                    temp = temp.replace(f"{{{{ {var_name}['{k}'] }}}}", str(v))
                rendered += temp
            result = result[:m.start()] + rendered + result[m.end():]
        else:
            break
    return result


def build_nav_links(has_devlog: bool, has_portfolio: bool) -> str:
    links = ['<a href="/CheeseV/">Home</a>']
    if has_devlog:
        links.append('<a href="devlog/">DevLog</a>')
    if has_portfolio:
        links.append('<a href="portfolio/">Portfolio</a>')
    return "\n    ".join(links)


def build_devlog(nav_links):
    posts = []
    posts_dir = os.path.join(CONTENT_DIR, 'devlog')
    if not os.path.isdir(posts_dir):
        return posts, {}

    posts_by_cat = {}
    for root, _, files in os.walk(posts_dir):
        for filename in sorted(files):
            if not filename.endswith('.md'):
                continue
            path = os.path.join(root, filename)
            md = read_file(path)
            lines = md.splitlines()
            title_line = lines[0]
            title = title_line.lstrip('#').strip()
            body_lines = lines[1:]
            date_str = None
            date_re = re.compile(r'\d{4}-\d{2}-\d{2}')
            for i, line in enumerate(body_lines):
                m = date_re.search(line)
                if m:
                    date_str = m.group(0)
                    body_lines.pop(i)
                    break
            body = simple_markdown('\n'.join(body_lines))
            rel_path = os.path.relpath(path, posts_dir)
            slug = os.path.splitext(rel_path)[0]
            content = render_template('post.html', title=title, date=date_str, body=body)
            page = render_template(
                'base.html',
                title=title,
                content=content,
                nav_links=nav_links,
                after_nav="",
            )
            output_path = os.path.join(OUTPUT_DIR, 'devlog', slug, 'index.html')
            write_file(output_path, page)
            item = {'title': title, 'link': f'devlog/{slug}/', 'date': date_str}
            posts.append(item)
            cat = os.path.relpath(root, posts_dir)
            if cat == '.':
                cat = ''
            posts_by_cat.setdefault(cat, []).append(item)

    if posts:
        sections = []
        if '' in posts_by_cat:
            items_html = []
            for p in posts_by_cat['']:
                disp = f"{p['title']} - {p['date']}" if p['date'] else p['title']
                items_html.append(f'<li><a href="{p["link"]}">{disp}</a></li>')
            sections.append('<ul>\n' + '\n'.join(items_html) + '\n</ul>')
        for cat in sorted(k for k in posts_by_cat.keys() if k):
            items_html = []
            for p in posts_by_cat[cat]:
                disp = f"{p['title']} - {p['date']}" if p['date'] else p['title']
                items_html.append(f'<li><a href="{p["link"]}">{disp}</a></li>')
            section = f'<h2>{cat}</h2>\n<ul>\n' + '\n'.join(items_html) + '\n</ul>'
            sections.append(section)
            cat_content = '<ul>\n' + '\n'.join(items_html) + '\n</ul>'
            cat_list = render_template(
                'devlog_list.html',
                title=SITE_NAME + ' - ' + 'DevLog',
                categories_content=cat_content,
            )
            cat_page = render_template(
                'base.html',
                title=SITE_NAME + ' - ' + cat,
                content=cat_list,
                nav_links=nav_links,
                after_nav="",
            )
            write_file(os.path.join(OUTPUT_DIR, 'devlog', cat, 'index.html'), cat_page)
        categories_content = '\n'.join(sections)
        list_content = render_template(
            'devlog_list.html',
            title=SITE_NAME + ' - ' + 'DevLog',
            categories_content=categories_content,
        )
        list_page = render_template(
            'base.html',
            title=SITE_NAME + ' - ' + 'DevLog',
            content=list_content,
            nav_links=nav_links,
            after_nav="",
        )
        write_file(os.path.join(OUTPUT_DIR, 'devlog', 'index.html'), list_page)
    return posts, posts_by_cat


def build_portfolio(nav_links):
    programs = []
    programs_dir = os.path.join(CONTENT_DIR, 'portfolio')
    if not os.path.isdir(programs_dir):
        return programs, {}

    programs_by_cat = {}
    for root, _, files in os.walk(programs_dir):
        for filename in sorted(files):
            path = os.path.join(root, filename)
            slug, ext = os.path.splitext(os.path.relpath(path, programs_dir))

            if ext == '.md':
                md = read_file(path)
                lines = md.splitlines()
                title_line = lines[0]
                title = title_line.lstrip('#').strip()
                body_lines = lines[1:]
                date_str = None
                date_re = re.compile(r'\d{4}-\d{2}-\d{2}')
                for i, line in enumerate(body_lines):
                    m = date_re.search(line)
                    if m:
                        date_str = m.group(0)
                        body_lines.pop(i)
                        break
                body = simple_markdown('\n'.join(body_lines))
            elif ext == '.html':
                html = read_file(path)
                m = re.search(r'<title>(.*?)</title>', html, re.S)
                if m:
                    title = m.group(1).strip()
                    body = html.replace(m.group(0), '').strip()
                else:
                    title = slug.replace('-', ' ').title()
                    body = html
            else:
                continue

            content = render_template('program.html', title=title, body=body)
            page = render_template(
                'base.html',
                title=title,
                content=content,
                nav_links=nav_links,
                after_nav="",
            )
            output_path = os.path.join(OUTPUT_DIR, 'portfolio', slug, 'index.html')
            write_file(output_path, page)
            item = {'title': title, 'link': f'portfolio/{slug}/'}
            programs.append(item)
            cat = os.path.relpath(root, programs_dir)
            if cat == '.':
                cat = ''
            programs_by_cat.setdefault(cat, []).append(item)

    if programs:
        sections = []
        if '' in programs_by_cat:
            items_html = []
            for p in programs_by_cat['']:
                items_html.append(f'<li><a href="{p["link"]}">{p["title"]}</a></li>')
            sections.append('<ul>\n' + '\n'.join(items_html) + '\n</ul>')
        for cat in sorted(k for k in programs_by_cat.keys() if k):
            items_html = []
            for p in programs_by_cat[cat]:
                items_html.append(f'<li><a href="{p["link"]}">{p["title"]}</a></li>')
            section = f'<h2>{cat}</h2>\n<ul>\n' + '\n'.join(items_html) + '\n</ul>'
            sections.append(section)
            cat_content = '<ul>\n' + '\n'.join(items_html) + '\n</ul>'
            cat_list = render_template(
                'list.html',
                title=SITE_NAME + ' - ' + 'Portfolio',
                categories_content=cat_content,
            )
            cat_page = render_template(
                'base.html',
                title=SITE_NAME + ' - ' + cat,
                content=cat_list,
                nav_links=nav_links,
                after_nav="",
            )
            write_file(os.path.join(OUTPUT_DIR, 'portfolio', cat, 'index.html'), cat_page)
        categories_content = '\n'.join(sections)
        list_content = render_template(
            'list.html',
            title=SITE_NAME + ' - ' + 'Portfolio',
            categories_content=categories_content,
        )
        list_page = render_template(
            'base.html',
            title=SITE_NAME + ' - ' + 'Portfolio',
            content=list_content,
            nav_links=nav_links,
            after_nav="",
        )
        write_file(os.path.join(OUTPUT_DIR, 'portfolio', 'index.html'), list_page)
    return programs, programs_by_cat


def build_sitemap(paths):
    """Generate sitemap.xml including the provided relative paths."""
    base_url = "https://cheesedongjin.github.io/CheeseV"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for p in paths:
        if p.endswith('index.html'):
            clean = p[:-10]
        elif p.endswith('.html'):
            clean = p[:-5]
        else:
            clean = p
        lines.append('  <url>')
        if clean:
            loc = f"{base_url}/{clean}"
        else:
            loc = f"{base_url}/"
        lines.append(f'    <loc>{loc}</loc>')
        lines.append('  </url>')
    lines.append('</urlset>')
    write_file(os.path.join(OUTPUT_DIR, 'sitemap.xml'), '\n'.join(lines))

def build_site():
    # Do not perform manually what this function handles automatically.
    # This is for GitHub management purposes.
    posts_dir = os.path.join(CONTENT_DIR, 'devlog')
    portfolio_dir = os.path.join(CONTENT_DIR, 'portfolio')

    def has_markdown_files(directory, exts):
        for root, _, files in os.walk(directory):
            for name in files:
                if any(name.endswith(ext) for ext in exts):
                    return True
        return False

    has_devlog = os.path.isdir(posts_dir) and has_markdown_files(posts_dir, ['.md'])
    has_portfolio = os.path.isdir(portfolio_dir) and has_markdown_files(
        portfolio_dir, ['.md', '.html']
    )

    nav_links = build_nav_links(has_devlog, has_portfolio)

    posts, posts_by_cat = build_devlog(nav_links) if has_devlog else ([], {})
    programs, programs_by_cat = build_portfolio(nav_links) if has_portfolio else ([], {})

    devlog_section = ''
    if posts:
        root_items = []
        if '' in posts_by_cat:
            for p in posts_by_cat['']:
                date_part = f' - {p["date"]}' if p['date'] else ''
                root_items.append(f'<li><a href="{p["link"]}">{p["title"]}</a>{date_part}</li>')
        for cat in sorted(k for k in posts_by_cat.keys() if k):
            items_html = []
            for p in posts_by_cat[cat]:
                date_part = f' - {p["date"]}' if p['date'] else ''
                items_html.append(f'<li><a href="{p["link"]}">{p["title"]}</a>{date_part}</li>')
            cat_ul = '<ul>\n' + '\n'.join(items_html) + '\n</ul>'
            root_items.append(f'<li><h3>{cat}</h3>\n{cat_ul}</li>')
        devlog_section = '<h2>DevLog</h2>\n<ul>\n' + '\n'.join(root_items) + '\n</ul>'

    portfolio_section = ''
    if programs:
        root_items = []
        if '' in programs_by_cat:
            for p in programs_by_cat['']:
                root_items.append(f'<li><a href="{p["link"]}">{p["title"]}</a></li>')
        for cat in sorted(k for k in programs_by_cat.keys() if k):
            items_html = []
            for p in programs_by_cat[cat]:
                items_html.append(f'<li><a href="{p["link"]}">{p["title"]}</a></li>')
            cat_ul = '<ul>\n' + '\n'.join(items_html) + '\n</ul>'
            root_items.append(f'<li><h3>{cat}</h3>\n{cat_ul}</li>')
        portfolio_section = '<h2>Portfolio</h2>\n<ul>\n' + '\n'.join(root_items) + '\n</ul>'

    index_content = render_template('index.html', devlog_section=devlog_section, portfolio_section=portfolio_section)
    index_page = render_template(
        'base.html',
        title=SITE_NAME,
        content=index_content,
        nav_links=nav_links,
        after_nav=""
    )
    write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_page)

    sitemap_entries = ['index.html', '404.html']
    if posts:
        sitemap_entries.append('devlog/index.html')
        for cat in posts_by_cat:
            if cat:
                sitemap_entries.append(f'devlog/{cat}/index.html')
        sitemap_entries.extend(p['link'] for p in posts)
    if programs:
        sitemap_entries.append('portfolio/index.html')
        sitemap_entries.extend(p['link'] for p in programs)
    build_sitemap(sitemap_entries)


if __name__ == '__main__':
    build_site()
    print('Site generated in', OUTPUT_DIR)
