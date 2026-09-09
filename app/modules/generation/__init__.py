from app.modules.generation.cover_letter import cover_letter_generator, CoverLetterGenerator
from app.modules.generation.resume_tailor import resume_tailorer, ResumeTailorer
from app.modules.generation.pdf_generator import resume_pdf_generator, ResumePdfGenerator
from app.modules.generation.question_answerer import question_answerer, QuestionAnswerer
from app.modules.generation.materials_pipeline import materials_pipeline, MaterialsPipeline

__all__ = [
    "cover_letter_generator",
    "CoverLetterGenerator",
    "resume_tailorer",
    "ResumeTailorer",
    "resume_pdf_generator",
    "ResumePdfGenerator",
    "question_answerer",
    "QuestionAnswerer",
    "materials_pipeline",
    "MaterialsPipeline"
]
