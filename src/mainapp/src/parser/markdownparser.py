


from mistune import create_markdown
def parse_markdown(md: str):
    ##TODO: deal with external links
    return create_markdown(escape=True,plugins=["strikethrough", "footnotes", "table"])(md)