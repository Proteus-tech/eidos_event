from django.db import models

from auth_client.auth_client_utils import get_current_user_url

class Event(models.Model):
    event_type = models.CharField(max_length=50)
    resource = models.URLField(max_length=500)
    project = models.URLField(max_length=500, blank=True, null=True) # we will use this to filter push updates, allow null because older events won't have
    data = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ('created_on',)

    def __unicode__(self):
        return u'%s event of %s on %s' % (self.event_type, self.resource, self.created_on)

    @models.permalink
    def get_absolute_url(self):
        return 'event', (), {'id': self.id}

    def save(self, *args, **kwargs):
        if self.id is None and not self.created_by:
            # created
            self.created_by = get_current_user_url()
        super(Event, self).save(*args, **kwargs)