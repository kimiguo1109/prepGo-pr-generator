"""Configuration settings for Practice Generator."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    gemini_api_key: str = ""
    
    # Model settings
    gemini_model: str = "gemini-2.5-flash"
    
    # Paths
    course_data_path: str = "/root/usr/prepGo_tool_forWeb/output/studyguide_rephrased"
    
    # S3 Storage settings
    use_s3_storage: bool = False
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # Course file mapping: course_id -> file path
    # Organized by category with standard URL-based course IDs
    course_file_mapping: dict = {
        # Math
        "precalculus": "stem-math/precalculus_complete_*.json",
        "calculus-ab": "stem-math/calculus-ab_complete_*.json",
        "calculus-bc": "stem-math/calculus-bc_complete_*.json",
        "statistics": "stem-math/statistics_complete_*.json",
        
        # Computer Science
        "computer-science-a": "compsci/computer-science-a_complete_*.json",
        "computer-science-principles": "compsci/computer-science-principles_complete_*.json",
        
        # Science
        "biology": "stem-science/biology_complete_*.json",
        "chemistry": "stem-science/chemistry_complete_*.json",
        "environmental-science": "stem-science/us-environment_complete_*.json",
        "physics-1": "stem-science/physics-1_complete_*.json",
        "physics-2": "stem-science/physics-2_complete_*.json",
        "physics-c-electricity-and-magnetism": "stem-science/physics-c-electricity_complete_*.json",
        "physics-c-mechanics": "stem-science/physics-c-mechanics_complete_*.json",
        
        # History
        "us-history": "socsci-history/us-history_complete_*.json",
        "world-history-modern": "socsci-history/modernworldhistory_complete_*.json",
        "european-history": "socsci-history/european-history_complete_*.json",
        
        # Social Science
        "macroeconomics": "socsci-economics/macroeconomics_complete_*.json",
        "microeconomics": "socsci-economics/microeconomics_complete_*.json",
        "us-government-and-politics": "socsci-other/us-gov-&-politics_complete_*.json",
        "comparative-government-and-politics": "socsci-other/comparative-government_complete_*.json",
        "psychology": "socsci-other/psychology_complete_*.json",
        "human-geography": "socsci-other/humangeo_complete_*.json",
        
        # Languages
        "spanish-language-and-culture": "worldlanguage/spanish_complete_*.json",
        "spanish-literature-and-culture": "worldlanguage/spanish-literature_complete_*.json",
        "latin": "worldlanguage/latin_complete_*.json",
        "chinese-language-and-culture": "worldlanguage/chinese_complete_*.json",
        "french-language-and-culture": "worldlanguage/french_complete_*.json",
        "german-language-and-culture": "worldlanguage/german_complete_*.json",
        "italian-language-and-culture": "worldlanguage/italian_complete_*.json",
        "japanese-language-and-culture": "worldlanguage/japanese_complete_*.json",
        
        # English
        "english-language-and-composition": "lang-comp/english-language_complete_*.json",
        "english-literature-and-composition": "lang-comp/english-literature_complete_*.json",
        
        # Arts
        "art-history": "arts/art-history_complete_*.json",
        "music-theory": "arts/music-thoery_complete_*.json",
    }
    
    # Course categories for organization
    course_categories: dict = {
        "math": [
            {"name": "AP Precalculus", "id": "precalculus"},
            {"name": "AP Calculus AB", "id": "calculus-ab"},
            {"name": "AP Calculus BC", "id": "calculus-bc"},
            {"name": "AP Statistics", "id": "statistics"},
            {"name": "AP Computer Science A", "id": "computer-science-a"},
            {"name": "AP Computer Science Principles", "id": "computer-science-principles"},
        ],
        "science": [
            {"name": "AP Biology", "id": "biology"},
            {"name": "AP Chemistry", "id": "chemistry"},
            {"name": "AP Environmental Science", "id": "environmental-science"},
            {"name": "AP Physics 1", "id": "physics-1"},
            {"name": "AP Physics 2", "id": "physics-2"},
            {"name": "AP Physics C: E&M", "id": "physics-c-electricity-and-magnetism"},
            {"name": "AP Physics C: Mechanics", "id": "physics-c-mechanics"},
        ],
        "history": [
            {"name": "AP U.S. History", "id": "us-history"},
            {"name": "AP World History: Modern", "id": "world-history-modern"},
            {"name": "AP European History", "id": "european-history"},
        ],
        "social_science": [
            {"name": "AP Macroeconomics", "id": "macroeconomics"},
            {"name": "AP Microeconomics", "id": "microeconomics"},
            {"name": "AP U.S. Government & Politics", "id": "us-government-and-politics"},
            {"name": "AP Comparative Government & Politics", "id": "comparative-government-and-politics"},
            {"name": "AP Psychology", "id": "psychology"},
            {"name": "AP Human Geography", "id": "human-geography"},
        ],
        "languages": [
            {"name": "AP Spanish Language", "id": "spanish-language-and-culture"},
            {"name": "AP Spanish Literature", "id": "spanish-literature-and-culture"},
            {"name": "AP Latin", "id": "latin"},
            {"name": "AP Chinese Language", "id": "chinese-language-and-culture"},
            {"name": "AP French Language", "id": "french-language-and-culture"},
            {"name": "AP German Language", "id": "german-language-and-culture"},
            {"name": "AP Italian Language", "id": "italian-language-and-culture"},
            {"name": "AP Japanese Language", "id": "japanese-language-and-culture"},
        ],
        "english": [
            {"name": "AP English Language", "id": "english-language-and-composition"},
            {"name": "AP English Literature", "id": "english-literature-and-composition"},
        ],
        "arts": [
            {"name": "AP Art History", "id": "art-history"},
            {"name": "AP Music Theory", "id": "music-theory"},
        ],
    }
    
    # Course type for special formatting
    course_type_mapping: dict = {
        # Math courses - heavy LaTeX
        "precalculus": "math",
        "calculus-ab": "math",
        "calculus-bc": "math",
        "statistics": "math",
        
        # Science courses - LaTeX for formulas
        "physics-1": "physics",
        "physics-2": "physics",
        "physics-c-electricity-and-magnetism": "physics",
        "physics-c-mechanics": "physics",
        "chemistry": "chemistry",
        "biology": "biology",
        "environmental-science": "science",
        
        # Computer Science
        "computer-science-a": "computer-science",
        "computer-science-principles": "computer-science",
        
        # History - document-based
        "us-history": "history",
        "world-history-modern": "history",
        "european-history": "history",
        
        # Economics - graphs and models
        "macroeconomics": "economics",
        "microeconomics": "economics",
        
        # Social Science
        "us-government-and-politics": "social-science",
        "comparative-government-and-politics": "social-science",
        "psychology": "social-science",
        "human-geography": "social-science",
        
        # Languages
        "spanish-language-and-culture": "language",
        "spanish-literature-and-culture": "language",
        "latin": "language",
        "chinese-language-and-culture": "language",
        "french-language-and-culture": "language",
        "german-language-and-culture": "language",
        "italian-language-and-culture": "language",
        "japanese-language-and-culture": "language",
        
        # English
        "english-language-and-composition": "english",
        "english-literature-and-composition": "english",
        
        # Arts
        "art-history": "art",
        "music-theory": "music",
    }
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 18300
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
