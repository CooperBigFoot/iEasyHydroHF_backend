import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from slugify import slugify


class CreatedDateMixin(models.Model):
    created_date = models.DateTimeField(verbose_name=_("Date created"), auto_now_add=True)

    class Meta:
        abstract = True


class LastModifiedDateMixin(models.Model):
    last_modified = models.DateTimeField(verbose_name=_("Modified date"), auto_now=True)

    class Meta:
        abstract = True


class CreateLastModifiedDateMixin(CreatedDateMixin, LastModifiedDateMixin):
    class Meta:
        abstract = True


class SlugMixin(models.Model):
    slug = models.SlugField(verbose_name=_("Slug"), max_length=255)

    class Meta:
        abstract = True

    @property
    def slug_source(self):
        """
        Override this in your model in case you want to generate
        the slug based on the value of another field.
        """
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self.get_slug()

        super().save(*args, **kwargs)

    def get_slug(self):
        return self.slug or slugify(self.slug_source)


class UUIDMixin(models.Model):
    uuid = models.UUIDField(verbose_name=_("UUID"), editable=False, default=uuid.uuid4, unique=True)

    class Meta:
        abstract = True


class ForecastToggleMixin(models.Model):
    daily_forecast = models.BooleanField(verbose_name=_("Enable daily forecast"), default=False)
    pentad_forecast = models.BooleanField(verbose_name=_("Enable pentad forecast"), default=False)
    decadal_forecast = models.BooleanField(verbose_name=_("Enable decadal forecast"), default=False)
    monthly_forecast = models.BooleanField(verbose_name=_("Enable monthly forecast"), default=False)
    seasonal_forecast = models.BooleanField(verbose_name=_("Enable seasonal forecast"), default=False)

    class Meta:
        abstract = True


class BulletinOrderMixin(models.Model):
    bulletin_order = models.PositiveIntegerField(verbose_name=_("Bulletin order"), default=0)

    class Meta:
        abstract = True
