# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Event.project'
        db.add_column('event_event', 'project', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Event.project'
        db.delete_column('event_event', 'project')


    models = {
        'event.event': {
            'Meta': {'ordering': "('created_on',)", 'object_name': 'Event'},
            'created_by': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'resource': ('django.db.models.fields.URLField', [], {'max_length': '500'})
        }
    }

    complete_apps = ['event']
