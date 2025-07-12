import os
from datetime import datetime

CONTENT_DIR = 'content'
OUTPUT_DIR = 'docs'
TEMPLATES_DIR = 'templates'


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


def build_devlog():
    posts = []
    posts_dir = os.path.join(CONTENT_DIR, 'devlog')
    for filename in sorted(os.listdir(posts_dir)):
        if filename.endswith('.md'):
            path = os.path.join(posts_dir, filename)
            md = read_file(path)
            title_line = md.splitlines()[0]
            title = title_line.lstrip('#').strip()
            body = simple_markdown('\n'.join(md.splitlines()[1:]))
            slug = os.path.splitext(filename)[0]
            date_str = datetime.now().strftime('%Y-%m-%d')
            content = render_template('post.html', title=title, date=date_str, body=body)
            page = render_template('base.html', title=title, content=content)
            output_path = os.path.join(OUTPUT_DIR, 'devlog', f'{slug}.html')
            write_file(output_path, page)
            posts.append({'title': title, 'link': f'/devlog/{slug}.html', 'date': date_str})
    # create post index
    list_content = render_template('list.html', title='DevLog', items=posts)
    list_page = render_template('base.html', title='DevLog', content=list_content)
    write_file(os.path.join(OUTPUT_DIR, 'devlog', 'index.html'), list_page)
    return posts


def build_portfolio():
    programs = []
    programs_dir = os.path.join(CONTENT_DIR, 'portfolio')
    for filename in sorted(os.listdir(programs_dir)):
        if filename.endswith('.md'):
            path = os.path.join(programs_dir, filename)
            md = read_file(path)
            title_line = md.splitlines()[0]
            title = title_line.lstrip('#').strip()
            body = simple_markdown('\n'.join(md.splitlines()[1:]))
            slug = os.path.splitext(filename)[0]
            content = render_template('program.html', title=title, body=body)
            page = render_template('base.html', title=title, content=content)
            output_path = os.path.join(OUTPUT_DIR, 'portfolio', f'{slug}.html')
            write_file(output_path, page)
            programs.append({'title': title, 'link': f'/portfolio/{slug}.html'})
    # create program index
    list_content = render_template('list.html', title='Web Portfolio', items=programs)
    list_page = render_template('base.html', title='Web Portfolio', content=list_content)
    write_file(os.path.join(OUTPUT_DIR, 'portfolio', 'index.html'), list_page)
    return programs


def update_readme(posts, programs):
    base_url = "https://cheesedongjin.github.io/CheeseV"
    header = (
        "# [CheeseV](https://cheesedongjin.github.io/CheeseV/)\n\n"
        "Hi, I'm Dongwook Lee — a passionate self‑taught developer from South Korea. "
        "I love building games, automating systems, and exploring new ideas through code.\n\n"
        "This repository contains a small Python script that generates my personal website. "
        "The site features two sections:\n\n"
        "* **DevLog** – a collection of short development posts\n"
        "* **Web Portfolio** – demos and links to my projects\n\n"
    )

    devlog_lines = ["## DevLog"]
    for post in posts:
        devlog_lines.append(f"- [{post['title']}]({base_url}{post['link']})")

    program_lines = ["## Web Portfolio"]
    for prog in programs:
        program_lines.append(f"- [{prog['title']}]({base_url}{prog['link']})")

    readme_content = header + "\n".join(devlog_lines) + "\n\n" + "\n".join(program_lines) + "\n"
    write_file("README.md", readme_content)


def build_site():
    posts = build_devlog()
    programs = build_portfolio()

    # regenerate index with programs list
    index_content = render_template('index.html', devlog=posts, portfolio=programs)
    index_page = render_template('base.html', title='Home', content=index_content)
    write_file(os.path.join(OUTPUT_DIR, 'index.html'), index_page)

    update_readme(posts, programs)


if __name__ == '__main__':
    build_site()
    print('Site generated in', OUTPUT_DIR)
