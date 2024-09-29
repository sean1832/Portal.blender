import bpy


class CustomHandler:
    @staticmethod
    def load(text_block_name, class_name, template_url=None) -> type:
        text_block = bpy.data.texts.get(text_block_name)
        if not text_block:
            raise ImportError(f"Text block '{text_block_name}' not found")
        module = {}
        exec(text_block.as_string(), module)
        if not module:
            raise ImportError("Module not found.")
        CustomHandler = module.get(class_name, None)
        if not CustomHandler:
            refer_to_template = (
                "" if not template_url else f" Please refer to template ({template_url})."
            )
            raise ImportError(f"{class_name} class not found.{refer_to_template}")
        return CustomHandler
