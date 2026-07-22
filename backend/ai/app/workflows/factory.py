from app.core.config import AISettings
from app.media.ffmpeg import FFmpegMediaProcessor
from app.providers.openai_compatible import OpenAICompatibleProvider
from app.providers.dashscope_asr import DashScopeAsrProvider
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill
from app.workflows.fitness_video_reconstruction import FitnessVideoReconstructionWorkflow


def build_video_workflow(settings: AISettings) -> FitnessVideoReconstructionWorkflow:
    settings.require_model_api()
    model_provider = OpenAICompatibleProvider(settings)
    asr_provider = DashScopeAsrProvider(settings)
    return FitnessVideoReconstructionWorkflow(
        media_processor=FFmpegMediaProcessor(
            settings.ffmpeg_path,
            settings.ffprobe_path,
        ),
        transcriber=asr_provider,
        video_analyzer=model_provider,
        text_recognizer=model_provider,
        action_card_skill=FitnessVideoToActionCardSkill(model_provider),
        media_output_dir=settings.media_output_dir,
        frame_interval_seconds=settings.frame_interval_seconds,
        max_frames=settings.max_frames,
    )
