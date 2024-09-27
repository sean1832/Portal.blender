from .operators.connections import register as _register_connections
from .operators.connections import unregister as _unregister_connections
from .operators.modal import register as _register_modal
from .operators.modal import unregister as _unregister_modal
from .operators.text_editor import register as _register_text_editor
from .operators.text_editor import unregister as _unregister_text_editor
from .panels.server_control import register as _register_server_control
from .panels.server_control import unregister as _unregister_server_control
from .properties.connection_properties import register as _register_connection_properties
from .properties.connection_properties import unregister as _unregister_connection_properties


def register():
    _register_connections()
    _register_modal()
    _register_text_editor()
    _register_server_control()
    _register_connection_properties()

def unregister():
    _unregister_connections()
    _unregister_modal()
    _unregister_text_editor()
    _unregister_server_control()
    _unregister_connection_properties()