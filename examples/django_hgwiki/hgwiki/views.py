from django.views.generic.simple import direct_to_template

def home(request, template_name='hgwiki/home.html'):
    """
    Returns hgwiki home page.
    """
    return direct_to_template(request, template=template_name)

