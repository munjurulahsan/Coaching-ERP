from django.contrib import admin
from .models import Batch, Coach, Client, Session, Payment

admin.site.register(Batch)
admin.site.register(Coach)
admin.site.register(Client)
admin.site.register(Session)
admin.site.register(Payment)
