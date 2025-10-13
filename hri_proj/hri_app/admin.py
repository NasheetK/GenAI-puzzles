from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(PuzzleImage)
class PuzzleImageAdmin(admin.ModelAdmin):
    list_display = ('img_id', 'img_path', 'timestamp')  # 显示成表格列
    search_fields = ('img_id', 'img_path')

admin.site.register(PuzzlePiece)
class PuzzlePieceAdmin(admin.ModelAdmin):
    list_display = ('piece_id', 'puzzle_image', 'piece_number', 'piece_path')
    search_fields = ('piece_path')

admin.site.register(PieceDragLog)
class PieceDragLogAdmin(admin.ModelAdmin):
    list_display = ('piece_id', 'x', 'y', 'timestamp', 'success')
    search_fields = ('piece_id')
