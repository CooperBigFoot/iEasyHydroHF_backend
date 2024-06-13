from django.db import models
from django.utils.translation import gettext_lazy as _

from sapphire_backend.utils.mixins.models import CreateLastModifiedDateMixin, UUIDMixin

from .choices import BulletinType
from .managers import BulletinTemplateQuerySet


def bulletin_upload_path(instance, filename):
    return f"bulletins/{instance.organization.uuid}/{instance.type}/{filename}"


class BulletinTemplate(UUIDMixin, CreateLastModifiedDateMixin, models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        related_name="bulletin_templates",
    )
    user = models.ForeignKey(
        "users.User", verbose_name=_("Uploader"), on_delete=models.PROTECT, related_name="uploaded_bulletin_templates"
    )
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    type = models.CharField(
        verbose_name=_("Value type"), choices=BulletinType, default=BulletinType.DAILY, max_length=2
    )
    filename = models.FileField(verbose_name=_("Bulletin file"), upload_to=bulletin_upload_path)
    is_deleted = models.BooleanField(verbose_name=_("Is deleted"), default=False)
    is_default = models.BooleanField(verbose_name=_("Is default?"), default=False)

    objects = BulletinTemplateQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Bulletin template")
        verbose_name_plural = _("Bulletin templates")
        ordering = ["-created_date"]
        indexes = [models.Index(fields=["uuid"], name="bulletin_template_uuid_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "type"],
                condition=models.Q(is_default=True),
                name="unique_default_per_organization_and_type",
            )
        ]


class BulletinTemplateTag(UUIDMixin, models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        to_field="uuid",
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        related_name="bulletin_template_tags",
    )
    name = models.CharField(verbose_name=_("Tag name"), max_length=200)
    description = models.TextField(verbose_name=_("Tag description"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Bulletin template tag")
        verbose_name_plural = _("Bulletin template tags")
        indexes = [models.Index(fields=["uuid"], name="bulletin_template_tag_uuid_idx")]
