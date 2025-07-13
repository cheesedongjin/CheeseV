import os
from datetime import datetime

CONTENT_DIR = 'content'
OUTPUT_DIR = 'docs'
TEMPLATES_DIR = 'templates'
SITE_NAME = 'CheeseV' + '-'


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
    in_list = False
    for line in lines:
        line = line.rstrip()
        if line.startswith('# '):
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
        elif line.startswith('## '):
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith('### '):
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if line:
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append('')
    if in_list:
        html_lines.append('</ul>')
    return '\n'.join(html_lines)


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
    links = ['<a href="index.html">Home</a>']
    if has_devlog:
        links.append('<a href="devlog/index.html">DevLog</a>')
    if has_portfolio:
        links.append('<a href="portfolio/index.html">Portfolio</a>')
    return "\n    ".join(links)


def automation_comment(section: str) -> str:
    return (
        f"<!-- Don't insert {section} section manually.\n"
        "The code will add it automatically.\n"
        "This is for GitHub management purposes.\n"
        "Never delete this comment. -->"
    )


def build_devlog(nav_links):
    posts = []
    posts_dir = os.path.join(CONTENT_DIR, 'devlog')
    if not os.path.isdir(posts_dir):
        return posts
    for filename in sorted(os.listdir(posts_dir)):
        if filename.endswith('.md'):
            path = os.path.join(posts_dir, filename)
            md = read_file(path)
            title_line = md.splitlines()[0]
            title = title_line.lstrip('#').strip()
            body = simple_markdown('\n'.join(md.splitlines()[1:]))
            slug = os.path.splitext(filename)[0]
            date_str = datetime.now().strftime('%Y-%m-%d')
            content = render_template('post.html', title=SITE_NAME+title, date=date_str, body=body)
            page = render_template(
                'base.html',
                title=SITE_NAME+title,
                content=content,
                nav_links=nav_links,
                after_nav=""
            )
            output_path = os.path.join(OUTPUT_DIR, 'devlog', f'{slug}.html')
            write_file(output_path, page)
            posts.append({'title': title, 'link': f'devlog/{slug}.html', 'date': date_str})
    if posts:
        list_content = render_template('list.html', title=SITE_NAME+'DevLog', items=posts)
        list_page = render_template(
            'base.html',
            title=SITE_NAME+'DevLog',
            content=list_content,
            nav_links=nav_links,
            after_nav=automation_comment('devlog')
        )
        write_file(os.path.join(OUTPUT_DIR, 'devlog', 'index.html'), list_page)
    return posts


def build_portfolio(nav_links):
    programs = []
    programs_dir = os.path.join(CONTENT_DIR, 'portfolio')
    if not os.path.isdir(programs_dir):
        return programs
    for filename in sorted(os.listdir(programs_dir)):
        path = os.path.join(programs_dir, filename)
        slug, ext = os.path.splitext(filename)

        if ext == '.md':
            md = read_file(path)
            title_line = md.splitlines()[0]
            title = title_line.lstrip('#').strip()
            body = simple_markdown('\n'.join(md.splitlines()[1:]))
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

        content = render_template('program.html', title=SITE_NAME+title, body=body)
        page = render_template(
            'base.html',
            title=SITE_NAME+title,
            content=content,
            nav_links=nav_links,
            after_nav=""
        )
        output_path = os.path.join(OUTPUT_DIR, 'portfolio', f'{slug}.html')
        write_file(output_path, page)
        programs.append({'title': title, 'link': f'portfolio/{slug}.html'})
    if programs:
        list_content = render_template('list.html', title=SITE_NAME+'Web Portfolio', items=programs)
        list_page = render_template(
            'base.html',
            title=SITE_NAME+'Web Portfolio',
            content=list_content,
            nav_links=nav_links,
            after_nav=automation_comment('portfolio')
        )
        write_file(os.path.join(OUTPUT_DIR, 'portfolio', 'index.html'), list_page)
    return programs


def build_site():
    # Do not perform manually what this function handles automatically.
    # This is for GitHub management purposes.
    posts_dir = os.path.join(CONTENT_DIR, 'devlog')
    portfolio_dir = os.path.join(CONTENT_DIR, 'portfolio')

    has_devlog = os.path.isdir(posts_dir) and any(f.endswith('.md') for f in os.listdir(posts_dir))
    has_portfolio = os.path.isdir(portfolio_dir) and any(
        f.endswith('.md') or f.endswith('.html')
        for f in os.listdir(portfolio_dir)
    )

    nav_links = build_nav_links(has_devlog, has_portfolio)

    posts = build_devlog(nav_links) if has_devlog else []
    programs = build_portfolio(nav_links) if has_portfolio else []

    devlog_section = ''
    if posts:
        items = '\n'.join(
            f'<li><a href="{p["link"]}">{p["title"]}</a> - {p["date"]}</li>' for p in posts
        )
        devlog_section = f'<h2>DevLog</h2>\n<ul>\n{items}\n</ul>'

    portfolio_section = ''
    if programs:
        items = '\n'.join(
            f'<li><a href="{p["link"]}">{p["title"]}</a></li>' for p in programs
        )
        portfolio_section = f'<h2>Web Portfolio</h2>\n<ul>\n{items}\n</ul>'

    index_content = render_template('index.html', devlog_section=devlog_section, portfolio_section=portfolio_section)
    index_page = render_template(
        'base.html',
        title=SITE_NAME+'Home',
        content=index_content,
        nav_links=nav_links,
        after_nav=""
    )
    write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_page)


if __name__ == '__main__':
    build_site()
    print('Site generated in', OUTPUT_DIR)
