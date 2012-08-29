# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Event'
        db.create_table('event_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('resource', self.gf('django.db.models.fields.URLField')(max_length=500)),
            ('data', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('created_by', self.gf('django.db.models.fields.URLField')(max_length=500, null=True, blank=True)),
        ))
        db.send_create_signal('event', ['Event'])


    def backwards(self, orm):
        
        # Deleting model 'Event'
        db.delete_table('event_event')


    models = {
        'event.event': {
            'Meta': {'ordering': "('created_on',)", 'object_name': 'Event'},
            'created_by': ('django.db.models.fields.URLField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resource': ('django.db.models.fields.URLField', [], {'max_length': '500'})
        }
    }

    complete_apps = ['event']
