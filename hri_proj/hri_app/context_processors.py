from django.conf import settings


def general_settings(request):
    return {
        "audio_puzzle": settings.AUDIO_PUZZLE,
        "audio_others": settings.AUDIO_OTHERS,
        "puzzle_pipeline": settings.PUZZLE_PIPELINE,
        "robot_enable": settings.ROBOT_ENABLE
    }