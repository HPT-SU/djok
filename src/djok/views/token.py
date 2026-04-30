import datetime

from django.db import transaction
from django.db.models import F
from django.views.generic import DetailView

from djok.models.token_base import TokenBase

__all__ = ['TokenViewBase']


class TokenViewBase(DetailView):
    slug_field = 'uid'
    slug_url_kwarg = 'token'

    confirm_field = 'uid2'
    confirm_url_kwarg = 'token2'

    object: TokenBase

    def success(self, request, *args, **kwargs):
        raise NotImplementedError

    def fail(self, request, *args, **kwargs):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        token: TokenBase = self.get_object()

        confirm = kwargs[self.confirm_url_kwarg]
        confirm_check = getattr(token, self.confirm_field)

        if confirm != confirm_check:
            return self.fail(request, *args, **kwargs)

        today = datetime.date.today()

        if today > token.expire:
            return self.fail(request, *args, **kwargs)

        # Атомарный check + increment под select_for_update. Без этого два
        # параллельных запроса по одной magic-link ссылке оба проходили
        # проверку (current_usage=0 < usage_limit=1) и оба увеличивали
        # счётчик — magic-link использовался дважды.
        with transaction.atomic():
            locked = type(token).objects.select_for_update().get(pk=token.pk)
            if 0 < locked.usage_limit <= locked.current_usage:
                return self.fail(request, *args, **kwargs)
            locked.current_usage = F('current_usage') + 1
            locked.save(update_fields=['current_usage'])
            self.object = locked

        return self.success(request, *args, **kwargs)
