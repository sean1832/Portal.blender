import bpy


def load_handler_from_text_block(text_block_name):
    text_block = bpy.data.texts.get(text_block_name)
    if not text_block:
        raise ImportError(f"Text block '{text_block_name}' not found")
    namespace = {}
    exec(text_block.as_string(), namespace)
    return namespace
