"""Конвертер CV: markdown -> чистый txt + HTML + PDF через Playwright.

Запуск: source .venv/bin/activate && python make_cv.py
"""
import re
import unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright

CV_DIR = Path(__file__).parent / "cv"
TEMPLATE_PATH = CV_DIR / "cv_template.html"

SOURCES = {
    "Maksim_Klimavets_CV_EN.md": "Maksim_Klimavets_CV_EN",
    "Maksim_Klimavets_CV_PL.md": "Maksim_Klimavets_CV_PL",
    "Maksim_Klimavets_CV_RU.md": "Maksim_Klimavets_CV_RU",
}

ICONS = {
    "email": '<svg viewBox="0 0 24 24"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "phone": '<svg viewBox="0 0 24 24"><path d="M3 5a2 2 0 012-2h2.28a1 1 0 01.94.725l.548 2.2a1 1 0 01-.252.834L7.09 7.49a15.11 15.11 0 006.422 6.422l1.248-1.248a1 1 0 01.834-.253l2.2.549a1 1 0 01.725.94V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "github": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.779-1.75-1.75s.784-1.75 1.75-1.75 1.75.779 1.75 1.75-.784 1.75-1.75 1.75zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>',
    "location": '<svg viewBox="0 0 24 24"><path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "visa": '<svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "general": '<svg viewBox="0 0 24 24"><path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>'
}

# ---------------------------------------------------------------------------
# TXT Генерация (сохраняем старый функционал без изменений)
# ---------------------------------------------------------------------------

class Line:
    def __init__(self, typ: str, text: str):
        self.typ = typ
        self.text = text

def strip_emoji(text: str) -> str:
    out = []
    for ch in text:
        cat = unicodedata.category(ch)
        code = ord(ch)
        if (0x1F000 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF
                or 0x1F1E6 <= code <= 0x1F1FF or code in (0xFE0F, 0x20E3)
                or cat == "So"):
            continue
        out.append(ch)
    return "".join(out)

def md_to_lines(md: str) -> list[Line]:
    lines: list[Line] = []
    for raw in md.splitlines():
        line = strip_emoji(raw).rstrip()
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        line = re.sub(r"`(.+?)`", r"\1", line)
        line = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", line)
        s = line.strip()
        if not s:
            lines.append(Line("blank", ""))
        elif s.startswith("# "):
            lines.append(Line("h1", s[2:].strip()))
        elif s.startswith("## "):
            lines.append(Line("h2", s[3:].strip()))
        elif s.startswith("### "):
            lines.append(Line("h2", s[4:].strip()))
        elif re.match(r"^-{3,}$", s):
            lines.append(Line("rule", ""))
        elif s.startswith("- ") or s.startswith("• "):
            lines.append(Line("bullet", s[2:].strip()))
        else:
            lines.append(Line("text", s))
    return lines

def to_txt(lines: list[Line]) -> str:
    out = []
    for ln in lines:
        if ln.typ == "h1":
            out.append(ln.text.upper())
            out.append("=" * len(ln.text))
        elif ln.typ == "h2":
            out.append("")
            out.append(ln.text.upper())
            out.append("-" * len(ln.text))
        elif ln.typ == "rule":
            out.append("-" * 50)
        elif ln.typ == "bullet":
            out.append(f"  - {ln.text}")
        elif ln.typ == "blank":
            out.append("")
        else:
            out.append(ln.text)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"

# ---------------------------------------------------------------------------
# HTML + Playwright PDF Генерация
# ---------------------------------------------------------------------------

def parse_contacts(lines: list[str]) -> list[dict]:
    items = []
    for line in lines:
        parts = re.split(r"·|\||--", line)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Clean Markdown bold/italic
            clean_part = part.replace("*", "").replace("_", "").strip()
            
            ctype = None
            val = clean_part
            
            if "@" in clean_part:
                ctype = "email"
                val = re.sub(r"^email:\s*", "", clean_part, flags=re.IGNORECASE)
            elif "github.com" in clean_part.lower():
                ctype = "github"
                val = re.sub(r"^github:\s*", "", clean_part, flags=re.IGNORECASE)
            elif "linkedin.com" in clean_part.lower():
                ctype = "linkedin"
                val = re.sub(r"^linkedin:\s*", "", clean_part, flags=re.IGNORECASE)
            elif "+" in clean_part or re.search(r"\+?\d{3,}\s\d{2,}", clean_part):
                ctype = "phone"
                val = re.sub(r"^phone:\s*", "", clean_part, flags=re.IGNORECASE)
            elif any(k in clean_part.lower() for k in ["visa", "виза", "wiza"]):
                ctype = "visa"
            elif any(k in clean_part.lower() for k in ["minsk", "минск", "belarus", "беларусь", "białoruś", "poland", "польша"]):
                ctype = "location"
                val = re.sub(r"^location:\s*", "", clean_part, flags=re.IGNORECASE)
            else:
                ctype = "general"
                
            # Strip starting emojis/symbols from value
            val = re.sub(r"^[^\w\s+]+", "", val).strip()
            
            if ctype:
                url = None
                if ctype == "email":
                    url = f"mailto:{val}"
                elif ctype == "github":
                    url = val if val.startswith("http") else f"https://{val}"
                elif ctype == "linkedin":
                    url = val if val.startswith("http") else f"https://{val}"
                elif ctype == "phone":
                    url = f"tel:{val.replace(' ', '')}"
                
                items.append({"type": ctype, "value": val, "url": url})
    return items

def parse_markdown_to_sections(md: str) -> tuple[str, str, list[dict], list[dict]]:
    lines = md.splitlines()
    name = ""
    role = ""
    contact_lines = []
    
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if line.startswith("# "):
            name = line[2:].strip()
            idx += 1
            break
        idx += 1
        
    while idx < len(lines):
        line = lines[idx].strip()
        # Fix: only skip bullet points starting with - or * or • followed by space
        is_bullet = line.startswith("- ") or line.startswith("* ") or line.startswith("• ")
        if line and not is_bullet and not line.startswith("##") and not line.startswith("---"):
            role = line.replace("*", "").strip()
            idx += 1
            break
        idx += 1
        
    while idx < len(lines):
        line = lines[idx].strip()
        if line.startswith("##"):
            break
        if line and not line.startswith("---"):
            contact_lines.append(line)
        idx += 1
        
    contacts = parse_contacts(contact_lines)
    
    sections = []
    current_section = None
    
    while idx < len(lines):
        line = lines[idx].strip()
        if line.startswith("## "):
            if current_section:
                sections.append(current_section)
            current_section = {
                "title": line[3:].strip(),
                "lines": []
            }
        elif current_section is not None:
            # Skip divider rules strictly
            if not line.startswith("---"):
                current_section["lines"].append(lines[idx])
        idx += 1
        
    if current_section:
        sections.append(current_section)
        
    return name, role, contacts, sections

def render_project_item(proj: dict) -> str:
    desc = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", proj["desc"])
    link_html = ""
    if proj["link"]:
        link_html = f'<a href="https://{proj["link"]}" class="project-link" target="_blank"><svg viewBox="0 0 24 24"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" stroke-linecap="round" stroke-linejoin="round"/></svg>{proj["link"]}</a>'
    return f'''
        <div class="project-item">
            <div class="project-header">
                <span class="project-title">{proj["title"]}</span>
                <span class="project-tech">{proj["stack"]}</span>
            </div>
            <p class="project-desc">{desc}</p>
            {link_html}
        </div>'''

def render_exp_item(exp: dict) -> str:
    bullets_html = ""
    if exp["bullets"]:
        bullets_html = '\n            <ul class="bullets">\n' + "".join(f'                <li>{b}</li>\n' for b in exp["bullets"]) + '            </ul>'
    return f'''
        <div class="exp-item">
            <div class="exp-header">
                <span class="exp-role">{exp["role"]}</span>
                <span class="exp-meta">{exp["company"]} &bull; {exp["date"]}</span>
            </div>{bullets_html}
        </div>'''

def render_edu_item(edu: dict) -> str:
    meta = f"{edu['location']} &bull; {edu['date']}" if edu['location'] else edu['date']
    return f'''
        <div class="edu-item">
            <div class="edu-header">
                <span class="edu-school">{edu["school"]}</span>
                <span class="edu-meta">{meta}</span>
            </div>
            <div class="edu-degree">{edu["degree"]}</div>
        </div>'''

def render_section_to_html(section: dict) -> str:
    title = section["title"]
    title_lower = title.lower()
    lines = section["lines"]
    
    content = "\n".join(lines).strip()
    if not content:
        return ""
        
    if any(k in title_lower for k in ["tech stack", "технологии", "stack"]):
        html = f'    <div class="section tech-stack">\n        <h2 class="section-title">{title}</h2>\n        <div class="tech-list">\n'
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            # Strip bullet marker only if it is followed by space
            if line_str.startswith("- ") or line_str.startswith("* ") or line_str.startswith("• "):
                line_str = line_str[2:].strip()
            
            m = re.match(r"\*\*(.+?)\*\*[:\s-]*(.+)$", line_str)
            if m:
                cat = m.group(1).strip()
                items_str = m.group(2).strip()
                items = [item.strip() for item in re.split(r",\s*", items_str) if item.strip()]
                pills_html = "".join(f'<span class="tech-pill">{it}</span>' for it in items)
                html += f'            <div class="tech-category"><span class="tech-category-name">{cat}</span><span class="tech-pills">{pills_html}</span></div>\n'
            else:
                html += f'            <div class="tech-category"><span class="tech-pill">{line_str}</span></div>\n'
        html += '        </div>\n    </div>\n'
        return html
        
    elif any(k in title_lower for k in ["projects", "проекты", "projekty"]):
        html = f'    <div class="section projects">\n        <h2 class="section-title">{title}</h2>\n        <div class="projects-list">\n'
        current_project = None
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            
            m = re.match(r"\*\*(.+?)\*\*[\s—\-]*\**([^*]+)\**", line_str)
            if m:
                if current_project:
                    html += render_project_item(current_project)
                stack = m.group(2).strip().strip("*").strip()
                current_project = {
                    "title": m.group(1).strip(),
                    "stack": stack,
                    "desc": "",
                    "link": ""
                }
            elif current_project:
                if "github.com" in line_str.lower():
                    clean_link = re.sub(r"^[^\w]*", "", line_str).strip()
                    current_project["link"] = clean_link
                else:
                    if current_project["desc"]:
                        current_project["desc"] += " " + line_str
                    else:
                        current_project["desc"] = line_str
                        
        if current_project:
            html += render_project_item(current_project)
        html += '\n        </div>\n    </div>\n'
        return html
        
    elif any(k in title_lower for k in ["experience", "опыт"]):
        html = f'    <div class="section experience">\n        <h2 class="section-title">{title}</h2>\n'
        current_exp = None
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if line_str.startswith("**") and "|" in line_str:
                if current_exp:
                    html += render_exp_item(current_exp)
                parts = [p.strip() for p in line_str.split("|")]
                role = parts[0].replace("**", "")
                company = parts[1] if len(parts) > 1 else ""
                date = parts[2] if len(parts) > 2 else ""
                current_exp = {
                    "role": role,
                    "company": company,
                    "date": date,
                    "bullets": []
                }
            elif current_exp:
                bullet_text = re.sub(r"^[-*•]\s*", "", line_str)
                current_exp["bullets"].append(bullet_text)
            else:
                html += f'        <p class="summary-text">{line_str}</p>\n'
                
        if current_exp:
            html += render_exp_item(current_exp)
        html += '    </div>\n'
        return html
        
    elif any(k in title_lower for k in ["education", "образование", "wykształcenie"]):
        html = f'    <div class="section education">\n        <h2 class="section-title">{title}</h2>\n'
        current_edu = None
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if line_str.startswith("**"):
                if current_edu:
                    html += render_edu_item(current_edu)
                current_edu = {
                    "school": line_str.replace("**", "").strip(),
                    "degree": "",
                    "date": "",
                    "location": ""
                }
            elif current_edu:
                parts = [p.strip() for p in line_str.split("|")]
                current_edu["degree"] = parts[0]
                if len(parts) > 1:
                    current_edu["date"] = parts[1]
                if len(parts) > 2:
                    current_edu["location"] = parts[2]
            else:
                html += f'        <p class="summary-text">{line_str}</p>\n'
                
        if current_edu:
            html += render_edu_item(current_edu)
        html += '    </div>\n'
        return html
        
    else:
        html = f'    <div class="section generic-{title_lower.replace(" ", "-")}">\n        <h2 class="section-title">{title}</h2>\n'
        in_list = False
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if line_str.startswith("- ") or line_str.startswith("* ") or line_str.startswith("• "):
                if not in_list:
                    html += '        <ul class="simple-list">\n'
                    in_list = True
                bullet_text = re.sub(r"^[-*•]\s*", "", line_str)
                bullet_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", bullet_text)
                html += f'            <li>{bullet_text}</li>\n'
            else:
                if in_list:
                    html += '        </ul>\n'
                    in_list = False
                line_str = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line_str)
                html += f'        <p class="summary-text">{line_str}</p>\n'
                
        if in_list:
            html += '        </ul>\n'
        html += '    </div>\n'
        return html

def build_html_cv(md: str) -> str:
    name, role, contacts, sections = parse_markdown_to_sections(md)
    
    contacts_html = ""
    for item in contacts:
        icon_svg = ICONS.get(item['type'], ICONS['general'])
        if item['url']:
            contacts_html += f'<span class="contact-item" data-type="{item["type"]}">{icon_svg}<a href="{item["url"]}" target="_blank">{item["value"]}</a></span>\n'
        else:
            contacts_html += f'<span class="contact-item" data-type="{item["type"]}">{icon_svg}<span>{item["value"]}</span></span>\n'
            
    content_html = ""
    for sec in sections:
        content_html += render_section_to_html(sec) + "\n"
        
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template
    html = html.replace("{{ name }}", name)
    html = html.replace("{{ role }}", role)
    html = html.replace("{{ contacts_html }}", contacts_html)
    html = html.replace("{{ content_html }}", content_html)
    
    return html

def compile_pdf(html_path: Path, pdf_path: Path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path.resolve()}")
        page.wait_for_load_state("networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        browser.close()

# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

def main() -> None:
    for src, stem in SOURCES.items():
        path = CV_DIR / src
        if not path.exists():
            print(f"SKIP (нет файла): {src}")
            continue
        
        md = path.read_text(encoding="utf-8")
        
        # 1. TXT
        lines = md_to_lines(md)
        txt_path = CV_DIR / f"{stem}.txt"
        txt_path.write_text(to_txt(lines), encoding="utf-8")
        print(f"TXT  -> {txt_path.name}")
        
        # 2. HTML
        html_content = build_html_cv(md)
        html_path = CV_DIR / f"{stem}.html"
        html_path.write_text(html_content, encoding="utf-8")
        print(f"HTML -> {html_path.name}")
        
        # 3. PDF via Playwright
        pdf_path = CV_DIR / f"{stem}.pdf"
        compile_pdf(html_path, pdf_path)
        print(f"PDF  -> {pdf_path.name}")

if __name__ == "__main__":
    main()
