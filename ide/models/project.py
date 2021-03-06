import shutil
import uuid

from django.contrib.auth.models import User
from django.db import models

from ide.models.files import ResourceFile, ResourceIdentifier, SourceFile
from ide.utils import generate_half_uuid

from ide.models.meta import IdeModel

__author__ = 'katharine'

class Project(IdeModel):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=50)
    last_modified = models.DateTimeField(auto_now_add=True)
    version_def_name = models.CharField(max_length=50, default="APP_RESOURCES")
    SDK_VERSIONS = (
        ('1', '1.1.2'),
        ('2', '2.0')
    )
    sdk_version = models.CharField(max_length=10, choices=SDK_VERSIONS, default='1')

    PROJECT_TYPES = (
        ('native', 'Native SDK'),
        ('simplyjs', 'Simply.JS')
    )
    project_type = models.CharField(max_length=10, choices=PROJECT_TYPES, default='native')

    # New settings for 2.0
    app_uuid = models.CharField(max_length=36, blank=True, null=True, default=generate_half_uuid)
    app_company_name = models.CharField(max_length=100, blank=True, null=True)
    app_short_name = models.CharField(max_length=100, blank=True, null=True)
    app_long_name = models.CharField(max_length=100, blank=True, null=True)
    app_version_code = models.IntegerField(blank=True, null=True, default=1)
    app_version_label = models.CharField(max_length=40, blank=True, null=True, default='1.0')
    app_is_watchface = models.BooleanField(default=False)
    app_capabilities = models.CharField(max_length=255, blank=True, null=True)
    app_keys = models.TextField(default="{}")
    app_jshint = models.BooleanField(default=True)

    app_capability_list = property(lambda self: self.app_capabilities.split(','))

    OPTIMISATION_CHOICES = (
        ('0', 'None'),
        ('1', 'Limited'),
        ('s', 'Prefer smaller'),
        ('2', 'Prefer faster'),
        ('3', 'Aggressive (faster, bigger)'),
    )

    optimisation = models.CharField(max_length=1, choices=OPTIMISATION_CHOICES, default='s')

    github_repo = models.CharField(max_length=100, blank=True, null=True)
    github_branch = models.CharField(max_length=100, blank=True, null=True)
    github_last_sync = models.DateTimeField(blank=True, null=True)
    github_last_commit = models.CharField(max_length=40, blank=True, null=True)
    github_hook_uuid = models.CharField(max_length=36, blank=True, null=True)
    github_hook_build = models.BooleanField(default=False)

    def get_last_build(self):
        try:
            return self.builds.order_by('-id')[0]
        except IndexError:
            return None

    def get_menu_icon(self):
        try:
            return self.resources.filter(is_menu_icon=True)[0]
        except IndexError:
            return None

    last_build = property(get_last_build)
    menu_icon = property(get_menu_icon)

    def __unicode__(self):
        return u"%s" % self.name



class TemplateProject(Project):
    KIND_TEMPLATE = 1
    KIND_SDK_DEMO = 2
    KIND_EXAMPLE = 3
    KIND_CHOICES = (
        (KIND_TEMPLATE, 'Template'),
        (KIND_SDK_DEMO, 'SDK Demo'),
        (KIND_EXAMPLE, 'Example')
    )

    template_kind = models.IntegerField(choices=KIND_CHOICES, db_index=True)

    def copy_into_project(self, project):
        uuid_string = ", ".join(["0x%02X" % ord(b) for b in uuid.uuid4().bytes])
        for resource in self.resources.all():
            new_resource = ResourceFile.objects.create(project=project, file_name=resource.file_name, kind=resource.kind)
            new_resource.save_string(resource.get_contents())
            for i in resource.identifiers.all():
                ResourceIdentifier.objects.create(resource_file=new_resource, resource_id=i.resource_id, character_regex=i.character_regex)

        for source_file in self.source_files.all():
            new_file = SourceFile.objects.create(project=project, file_name=source_file.file_name)
            new_file.save_file(source_file.get_contents().replace("__UUID_GOES_HERE__", uuid_string))

        # Copy over relevant project properties.
        # NOTE: If new, relevant properties are added, they must be copied here.
        # todo: can we do better than that? Maybe we could reuse the zip import mechanism or something...
        if self.sdk_version != '1':
            project.app_capabilities = self.app_capabilities
            project.app_is_watchface = self.app_is_watchface
            project.app_keys = self.app_keys
            project.app_jshint = self.app_jshint
            project.save()