from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def styled_button(text, button_type="primary", size="md", onclick="", disabled=False, **kwargs):
    """
    Composant bouton stylisé réutilisable avec texte personnalisable
    """
    # Classes de base
    base_classes = "font-medium rounded-lg focus:ring-4 focus:outline-none"
    
    # Classes par type
    type_classes = {
        "primary": "text-white bg-teal-700 hover:bg-teal-800 focus:ring-teal-300 dark:bg-teal-600 dark:hover:bg-teal-700 dark:focus:ring-teal-800",
        "secondary": "text-gray-900 bg-white border border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:ring-gray-200 dark:focus:ring-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700",
        "danger": "text-white bg-red-700 hover:bg-red-800 focus:ring-red-300 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-800",
        "success": "text-white bg-green-700 hover:bg-green-800 focus:ring-green-300 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800"
    }
    
    # Classes par taille
    size_classes = {
        "sm": "text-xs px-3 py-1.5",
        "md": "text-sm px-5 py-2.5",
        "lg": "text-base px-6 py-3"
    }
    
    # Classes de désactivation
    disabled_classes = "opacity-50 cursor-not-allowed" if disabled else ""
    
    # Construction des classes
    classes = f"{base_classes} {type_classes.get(button_type, type_classes['primary'])} {size_classes.get(size, size_classes['md'])} {disabled_classes}"
    
    # Attributs HTML
    attributes = []
    if onclick:
        attributes.append(f'onclick="{onclick}"')
    if disabled:
        attributes.append('disabled')
    
    # Attributs supplémentaires
    for key, value in kwargs.items():
        if key.startswith('data_'):
            attributes.append(f'{key.replace("_", "-")}="{value}"')
        elif key != 'class':
            attributes.append(f'{key}="{value}"')
    
    attributes_str = ' '.join(attributes)
    
    # Génération du HTML
    button_html = f'<button type="submit" class="{classes}" {attributes_str}>{text}</button>'
    
    return mark_safe(button_html)


