from django import template
from markdown import markdown
import bleach

register = template.Library()


@register.filter(name='render_markdown')
def render_markdown(text):
    # Convert markdown to HTML with safe extensions
    html = markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])
    
    # Sanitize HTML to prevent XSS attacks
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'hr',
        'code', 'pre', 'blockquote', 'ul', 'ol', 'li',
        'strong', 'em', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]
    allowed_attributes = {
        'a': ['href', 'title'],
        'code': ['class'],
        'pre': ['class']
    }
    
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return clean_html 