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


admin.site.register(PersonalRecordDetail)
class PersonalRecordDetail(admin.ModelAdmin):
    list_display = ('detail_id', 'name', 'puzzle_id', 'action', 'timestamp')
    search_fields = ('name', 'puzzle_id')


admin.site.register(PersonalRecordGeneral)
class PersonalRecordGeneral(admin.ModelAdmin):
    list_display = ('record_id', 'name', 'team_member', 'game_mode',
                    'difficulty', 'character', 'bg_color',
                    'puzzle_amount', 'time_start', 'time_end',
                    'self_feeling_score', 'self_task_score', 'ai_task_score')
    search_fields = ('name', 'puzzle_id')
