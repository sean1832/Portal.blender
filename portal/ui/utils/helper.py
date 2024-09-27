def is_connection_duplicated(connections, name_to_check, uuid_to_ignore=None):
    """Helper function to check if a connection name is duplicated"""
    for conn in connections:
        if conn.name == name_to_check and conn.uuid != uuid_to_ignore:
            return True
    return False