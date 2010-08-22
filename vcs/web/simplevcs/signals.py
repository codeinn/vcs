from django.dispatch import Signal

pre_clone = Signal(providing_args=['repo_path', 'ip', 'username'])
pre_push = Signal(providing_args=['repo_path', 'ip', 'username'])
post_clone = Signal(providing_args=['repo_path', 'ip', 'username'])
post_push = Signal(providing_args=['repo_path', 'ip', 'username'])

retrieve_hg_post_push_messages = Signal(providing_args=['repository'])

