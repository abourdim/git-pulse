"""Simple template engine — {{variable}} replacement, loops, conditionals."""

import re
import os
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


def render(template_name: str, **ctx) -> str:
    path = TEMPLATES_DIR / template_name
    if not path.exists():
        return f"<h1>Template not found: {template_name}</h1>"
    html = path.read_text(encoding="utf-8")
    return _process(html, ctx)


def _process(html: str, ctx: dict) -> str:
    # Includes: {{include header.html}}
    def do_include(m):
        inc_name = m.group(1).strip()
        inc_path = TEMPLATES_DIR / inc_name
        if inc_path.exists():
            return inc_path.read_text(encoding="utf-8")
        return f"<!-- missing: {inc_name} -->"
    html = re.sub(r"\{\{include\s+(.+?)\}\}", do_include, html)

    # Loops: {{for item in items}} ... {{endfor}}
    def do_loop(m):
        var = m.group(1).strip()
        collection = m.group(2).strip()
        body = m.group(3)
        items = ctx.get(collection, [])
        out = []
        for item in items:
            local = {**ctx, var: item}
            out.append(_replace_vars(body, local))
        return "".join(out)
    html = re.sub(r"\{\{for\s+(\w+)\s+in\s+(\w+)\}\}(.*?)\{\{endfor\}\}", do_loop, html, flags=re.DOTALL)

    # Conditionals: {{if var}} ... {{else}} ... {{endif}}
    def do_if(m):
        var = m.group(1).strip()
        true_block = m.group(2)
        else_block = m.group(4) or ""
        val = ctx.get(var)
        if val:
            return _replace_vars(true_block, ctx)
        return _replace_vars(else_block, ctx)
    html = re.sub(r"\{\{if\s+(\w+)\}\}(.*?)(\{\{else\}\}(.*?))?\{\{endif\}\}", do_if, html, flags=re.DOTALL)

    return _replace_vars(html, ctx)


def _replace_vars(html: str, ctx: dict) -> str:
    def replacer(m):
        key = m.group(1).strip()
        # Support dotted access: item.name
        parts = key.split(".")
        val = ctx
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, "")
            else:
                val = getattr(val, p, "")
        if val is None:
            return ""
        return str(val)
    return re.sub(r"\{\{(\w[\w.]*)\}\}", replacer, html)
