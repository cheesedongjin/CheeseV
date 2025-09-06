import os
import re

try:
    import markdown
except ImportError:
    markdown = None


def md_to_html(text: str) -> str:
    """Convert markdown text to HTML."""
    if markdown is None:
        return text
    return markdown.markdown(text, extensions=["fenced_code", "tables"])

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


def render_template(template_name, **context):
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    template = read_file(template_path)

    # very small template engine using {{ var }} and {% for %}
    result = template
    for key, value in context.items():
        if isinstance(value, str):
            result = result.replace(f"{{{{ {key} }}}}", value)
    # handle loops
    import re
    pattern = re.compile(r'{% for (\w+) in (\w+) %}(.*?){% endfor %}', re.S)
    while True:
        m = pattern.search(result)
        if not m:
            break
        var_name, list_name, body = m.groups()
        items = context.get(list_name, [])
        rendered = ''
        for item in items:
            temp = body
            for k, v in item.items():
                temp = temp.replace(f"{{{{ {var_name}['{k}'] }}}}", str(v))
            rendered += temp
        result = result[:m.start()] + rendered + result[m.end():]
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
            body = md_to_html('\n'.join(body_lines))
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
                title_line = md.splitlines()[0]
                title = title_line.lstrip('#').strip()
                body = md_to_html('\n'.join(md.splitlines()[1:]))
            elif ext == '.html':
                html = read_file(path)
                import re
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
