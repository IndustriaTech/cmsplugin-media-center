from django.contrib import admin
from django.conf.urls import patterns, url
from django.shortcuts import redirect, Http404


class ActionsForObjectAdmin(admin.ModelAdmin):
    """
    Adds some urls that can call an action for given object.

    Example:
        if url is /admin/myapp/mymodel/object_id/
        and if I have a declatered action named 'my_action'
        if I open a url /admin/myapp/mymodel/object_id/action/my_action/
        then 'my_action' will be executed for object from myapp.mymodel
        with pk=object_id
    """
    def actions_view(self, request, object_id, action):
        """
        Add a method that handle actions for given object id
        This is done because we dont wont to send post for do action for one element
        """
        queryset = self.queryset(request).filter(pk=object_id)
        if queryset.exists():
            action = self.get_action(action)
            if action:
                action[0](self, request, queryset)
                opts = self.model._meta
                return redirect('admin:%s_%s_change' % (opts.app_label, opts.module_name), object_id)
        raise Http404

    def get_urls(self):
        """
        Adds url for action view
        """
        info = self.model._meta.app_label, self.model._meta.module_name

        urls = patterns(
            '',
            url(r'^(.+)/action/([\w]+)/$',
                self.admin_site.admin_view(self.actions_view),
                name='%s_%s_actions' % info,
                ),
        ) + super(ActionsForObjectAdmin, self).get_urls()
        return urls
