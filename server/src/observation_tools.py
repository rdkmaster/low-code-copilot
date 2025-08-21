
from .page_state import get_current_page_schema

# --- Helper function for recursive search ---
def _find_component_by_id_recursive(schema, component_id):
    if schema.get('id') == component_id:
        return schema
    if 'children' in schema:
        for child in schema['children']:
            found = _find_component_by_id_recursive(child, component_id)
            if found:
                return found
    return None

def _find_components_recursive(schema, filters, parent_id, results):
    # Check if the current component matches the parent_id if specified
    if parent_id is None or schema.get('id') == parent_id:
        # If we are inside the correct parent (or if no parent is specified),
        # check if the component matches the filters.
        matches = True
        for f in filters:
            prop_value = schema.get('props', {}).get(f['property'])
            if prop_value != f['value']:
                matches = False
                break
        if matches:
            results.append(schema)

        # If we found the parent, we should only search its direct children
        if parent_id is not None and schema.get('id') == parent_id:
            if 'children' in schema:
                for child in schema['children']:
                    _find_components_recursive(child, filters, None, results)
            return # Stop further recursion down this path

    # Continue searching in children if we haven't found the parent yet
    if 'children' in schema:
        for child in schema['children']:
            _find_components_recursive(child, filters, parent_id, results)


# --- Core Observation Tools ---

def get_page_outline():
    """ 
    Gets the entire page's component tree structure, without detailed properties.
    Used for quick understanding of page layout and component hierarchy.
    """
    schema = get_current_page_schema()
    def strip_props(node):
        new_node = {"id": node['id'], "type": node['type']}
        if 'children' in node and node['children']:
            new_node['children'] = [strip_props(child) for child in node['children']]
        return new_node
    return strip_props(schema)

def get_component_details(component_id: str):
    """
    Gets all the detailed properties of a component by its ID.
    """
    schema = get_current_page_schema()
    component = _find_component_by_id_recursive(schema, component_id)
    if component:
        return {
            "id": component.get("id"),
            "type": component.get("type"),
            "properties": component.get("props", {})
        }
    return None

def find_components(parent_id: str = None, filters: list = []):
    """
    Finds a list of components based on conditions (e.g., component type, property value, parent ID).
    """
    schema = get_current_page_schema()
    results = []
    _find_components_recursive(schema, filters, parent_id, results)
    return results
