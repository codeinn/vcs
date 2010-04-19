from vcs.web.simplevcs.utils import is_mercurial

import pagination.middleware

class PaginationMiddleware(pagination.middleware.PaginationMiddleware):
    """
    Inserts a variable representing the current page onto the request object if
    it exists in either **GET** or **POST** portions of the request.  This,
    slightly modified version of original
    ``pagination.middleware.PaginationMiddleware`` won't break ``mercurial``
    requests.
    """
    def process_request(self, request):
        if is_mercurial(request):
            # Won't continue on mercurial request as
            # it would break the response
            return
        super(PaginationMiddleware, self).process_request(request)


