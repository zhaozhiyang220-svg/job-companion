def render_pdf(html: str) -> bytes:
    # 延迟导入：WeasyPrint 依赖原生 GTK/Pango 库；本机（Windows）无库时仅在调用处失败，
    # 不影响模块/路由导入。CI(Linux) 装好 apt 依赖后可正常渲染。
    from weasyprint import HTML

    result: bytes = HTML(string=html).write_pdf()
    return result
