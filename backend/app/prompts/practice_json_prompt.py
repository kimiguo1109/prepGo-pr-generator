"""Practice generation prompt template for JSON output with subject-specific formatting."""
from typing import Optional
from app.models.course import Unit
from app.models.practice import DifficultyLevel


# Subject-specific formatting instructions
SUBJECT_FORMATTING = {
    "math": """
## Math-Specific Formatting
- Use LaTeX for ALL mathematical expressions: $x^2$, $\\frac{a}{b}$, $\\int_0^1 f(x)dx$, $\\sqrt{x}$
- Use display math for complex equations: $$\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$$
- Properly format derivatives: $\\frac{dy}{dx}$, $f'(x)$, $\\frac{d^2y}{dx^2}$
- Format matrices: $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$
- Use proper notation for trigonometric functions: $\\sin$, $\\cos$, $\\tan$
- Include coordinate pairs as $(x, y)$
- Format inequalities properly: $\\leq$, $\\geq$, $\\neq$
""",
    
    "physics": """
## Physics-Specific Formatting
- Use LaTeX for ALL formulas: $F = ma$, $E = mc^2$, $V = IR$
- Include units with values: "5 m/s" or "$5 \\ \\text{m/s}$"
- Format vectors properly: $\\vec{v}$, $\\vec{F}$, $|\\vec{v}|$
- Use subscripts for variables: $v_0$, $a_x$, $F_{net}$
- Format common physics equations:
  - Kinematics: $x = x_0 + v_0 t + \\frac{1}{2}at^2$
  - Energy: $KE = \\frac{1}{2}mv^2$, $PE = mgh$
  - Electricity: $F = k\\frac{q_1 q_2}{r^2}$
- Include free-body diagram descriptions in text when relevant
""",
    
    "chemistry": """
## Chemistry-Specific Formatting
- Use LaTeX for chemical formulas with subscripts: $H_2O$, $CO_2$, $C_6H_{12}O_6$
- Format chemical equations: $2H_2 + O_2 \\rightarrow 2H_2O$
- Use proper notation for ions: $Na^+$, $Cl^-$, $SO_4^{2-}$
- Format equilibrium constants: $K_a$, $K_b$, $K_{sp}$, $K_w$
- Include reaction arrows: $\\rightarrow$, $\\leftarrow$, $\\rightleftharpoons$
- Format electron configurations: $1s^2 2s^2 2p^6$
- Use proper units: mol, L, M (molarity), kJ/mol
- Format pH calculations: $pH = -\\log[H^+]$
""",
    
    "biology": """
## Biology-Specific Formatting
- Use italics for scientific names: *Homo sapiens*, *E. coli*
- Format chemical formulas when needed: $ATP$, $CO_2$, $O_2$
- Use proper notation for reactions: photosynthesis, cellular respiration
- Include gene notation when relevant: dominant (A), recessive (a)
- Format Punnett square results in clear tables
- Use subscripts for biological molecules: $NAD^+$, $NADH$, $FAD$
""",
    
    "economics": """
## Economics-Specific Formatting
- Use LaTeX for economic formulas: $GDP = C + I + G + (X - M)$
- Format elasticity: $E_d = \\frac{\\%\\Delta Q_d}{\\%\\Delta P}$
- Use proper currency notation: dollars (as text, not LaTeX)
- Format graphs/models descriptions clearly
- Include supply/demand notation: $Q_s$, $Q_d$, $P^*$ (equilibrium)
- Format marginal analysis: $MC$, $MR$, $MB$, $MC$
- Use subscripts for time periods: $Y_t$, $P_{t+1}$
""",
    
    "history": """
## History-Specific Formatting
- Include primary source excerpts in quotation blocks
- Format dates clearly: "1776", "1861-1865"
- Use proper citation format for historical documents
- Include document context (author, date, purpose)
- For DBQ questions, provide document excerpts with source attribution
- Use historical terminology accurately
""",
    
    "computer-science": """
## Computer Science-Specific Formatting
- Format code snippets with proper syntax:
  ```java
  public static void method() { }
  ```
- Use monospace for code elements: `variable`, `methodName()`, `ClassName`
- Format Big-O notation: $O(n)$, $O(n^2)$, $O(\\log n)$
- Include pseudocode when appropriate
- Format boolean expressions: `true`, `false`, `&&`, `||`, `!`
- Use proper data structure notation: arrays `int[]`, ArrayList, HashMap
""",
    
    "language": """
## Language-Specific Formatting
- Include target language text with proper accents/characters
- Provide English translations where needed
- Format dialogues/passages clearly
- Use proper punctuation for the target language
- Include cultural context notes when relevant
- Format reading comprehension passages as quotation blocks
""",
    
    "english": """
## English-Specific Formatting
- Include literary passages as quotation blocks with proper attribution
- Use proper citation format (author, title, date)
- Format rhetorical terms in italics when introduced
- Include line numbers for poetry references
- Format essay prompts with clear thesis requirements
- Use quotation marks for short excerpts, block quotes for longer passages
""",
    
    "music": """
## Music Theory-Specific Formatting
- Use proper notation for chords: I, IV, V, vi, ii°
- Format time signatures: 4/4, 3/4, 6/8
- Include scale degree notation: $\\hat{1}$, $\\hat{5}$
- Format intervals: M3, P5, m7
- Use Italian terms properly: *forte*, *piano*, *allegro*
- Format key signatures: C major, G minor, etc.
""",
    
    "art": """
## Art History-Specific Formatting
- Include artwork titles in italics: *Starry Night*, *David*
- Format artist names and dates: "Leonardo da Vinci (1452-1519)"
- Include movement/period names: Renaissance, Baroque, Impressionism
- Reference specific visual elements in descriptions
- Include medium and dimensions when relevant
""",
    
    "social-science": """
## Social Science-Specific Formatting
- Include proper terminology definitions
- Format case study references clearly
- Use data and statistics with proper citations
- Include graph/chart descriptions
- Format government structure diagrams in text
- Reference constitutional provisions accurately
""",
    
    "science": """
## General Science Formatting
- Use LaTeX for formulas and equations
- Include proper units with measurements
- Format scientific notation: $3.0 \\times 10^8$ m/s
- Use subscripts/superscripts appropriately
- Include diagram descriptions when needed
""",
    
    "general": """
## General Formatting
- Use clear, professional language
- Format key terms appropriately
- Include proper citations and references
- Use LaTeX for any mathematical expressions
"""
}


PRACTICE_JSON_PROMPT_TEMPLATE = """
# Role and Objective
You are an **AP Exam Design Expert** and a master of the **Course and Exam Description (CED)** guidelines.
Your task is to design a high-quality **Practice Question Set** for **{course_name}**, covering the following units:
{unit_list}

# Subject Type: {course_type}
{subject_formatting}

# Output Format: JSON ONLY
**CRITICAL:** You MUST output ONLY valid JSON. No markdown, no explanations, no extra text before or after the JSON.

# Difficulty Setting: {difficulty_level}
{difficulty_guidance}

# Units Content Reference
{units_content}

# JSON Schema
Output a JSON object with this exact structure:

{{
  "header": {{
    "course_name": "string",
    "units_covered": ["Unit 1: Title", "Unit 2: Title"],
    "difficulty_level": "easier|ap_level|harder",
    "total_mcq": number,
    "total_frq": number
  }},
  "mcq_questions": [
    {{
      "number": 1,
      "stimulus": "Optional stimulus text (passage, data, scenario). Use null if no stimulus. For math/physics, include LaTeX formulas.",
      "question": "The question text with proper formatting (LaTeX for math, etc.)",
      "options": {{
        "A": "First option (with LaTeX if needed)",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "B",
      "explanation": "Why B is correct and why other options are incorrect (with LaTeX for calculations)"
    }}
  ],
  "frq_questions": [
    {{
      "number": 1,
      "type": "SAQ|LEQ|DBQ|Data Analysis|Calculation|etc",
      "stimulus": "Optional stimulus (equations, data, documents, code). Use null if none.",
      "parts": [
        {{
          "part": "a",
          "task_verb": "Calculate|Describe|Explain|etc",
          "prompt": "The question prompt with proper formatting",
          "points": 1
        }}
      ],
      "model_answer": {{
        "a": "Model answer with proper formatting (show work for calculations)"
      }},
      "scoring_guidelines": {{
        "a": "1 point for..."
      }},
      "total_points": 3
    }}
  ],
  "answer_key": {{
    "mcq": [
      {{"number": 1, "answer": "B"}}
    ]
  }}
}}

# Requirements

## MCQ Questions ({mcq_count} total)
- Generate EXACTLY {mcq_count} MCQ questions
- Each question MUST have options A, B, C, D
- Use proper formatting for this subject type (see Subject-Specific Formatting above)
- NO image references - use text descriptions only

## FRQ Questions ({frq_count} total)
- Generate EXACTLY {frq_count} FRQ questions
- Use appropriate FRQ types for {course_type} subject
- Include model answers with FULL WORK SHOWN for calculations
- Use proper formatting for this subject type

## Content Guidelines
- Align with CED Learning Objectives and Essential Knowledge
- Match the specified difficulty level: {difficulty_description}
- For calculations: Show step-by-step work in model answers
- For science/math: Use LaTeX for ALL formulas and equations

# CRITICAL REMINDERS
1. Output ONLY the JSON object - no markdown code blocks, no explanations
2. Ensure the JSON is valid and parseable
3. Include ALL {mcq_count} MCQ questions and {frq_count} FRQ questions
4. Use proper formatting for {course_type} subject throughout
5. For math/physics: ALWAYS use LaTeX: $formula$

Generate the complete JSON now:
"""


def get_difficulty_description(difficulty: DifficultyLevel) -> tuple[str, str]:
    """Get difficulty level description and guidance."""
    if difficulty == DifficultyLevel.EASIER:
        return (
            "Easier than AP Exam",
            """- Focus on foundational concepts and straightforward applications
- Use simpler language and shorter stimuli
- Avoid multi-step reasoning questions
- Distractors should be more obviously incorrect"""
        )
    elif difficulty == DifficultyLevel.HARDER:
        return (
            "Harder than AP Exam",
            """- Include more complex, multi-step reasoning questions
- Use longer and more nuanced stimuli
- Require synthesis across multiple concepts
- Distractors should be very plausible"""
        )
    else:  # AP_LEVEL
        return (
            "AP Exam Level",
            """- Match the exact difficulty of official AP exam questions
- Use authentic stimulus materials
- Balance recall, application, and analysis questions
- Distractors should reflect common misconceptions"""
        )


def get_subject_formatting(course_type: str) -> str:
    """Get subject-specific formatting instructions."""
    return SUBJECT_FORMATTING.get(course_type, SUBJECT_FORMATTING["general"])


def build_practice_json_prompt(
    units: list[Unit],
    course_name: str,
    mcq_count: int,
    frq_count: int,
    difficulty: DifficultyLevel,
    course_type: str = "general",
    skills_dict: dict = None
) -> str:
    """Build the practice generation prompt for JSON output with subject-specific formatting."""
    
    # Build unit list
    unit_list = "\n".join([f"- **Unit {u.unit_number}:** {u.unit_title}" for u in units])
    
    # Get difficulty description and guidance
    difficulty_description, difficulty_guidance = get_difficulty_description(difficulty)
    
    # Get subject-specific formatting
    subject_formatting = get_subject_formatting(course_type)
    
    # Build units content (condensed for JSON prompt)
    units_content = ""
    for unit in units:
        units_content += f"\n## Unit {unit.unit_number}: {unit.unit_title}\n"
        
        if unit.exam_weight:
            units_content += f"**Exam Weight:** {unit.exam_weight}\n"
        
        # Add topics with learning objectives
        for topic in unit.topics:
            units_content += f"\n### {topic.topic_number}: {topic.topic_title}\n"
            
            if topic.learning_objectives:
                units_content += "**Learning Objectives:**\n"
                for lo in topic.learning_objectives[:3]:
                    units_content += f"- {lo.id}: {lo.summary}\n"
            
            if topic.essential_knowledge:
                units_content += "**Essential Knowledge:**\n"
                for ek in topic.essential_knowledge[:3]:
                    units_content += f"- {ek.id}: {ek.summary}\n"
    
    # Build final prompt
    prompt = PRACTICE_JSON_PROMPT_TEMPLATE.format(
        course_name=course_name,
        course_type=course_type,
        unit_list=unit_list,
        difficulty_level=difficulty.value.upper().replace("_", " "),
        difficulty_description=difficulty_description,
        difficulty_guidance=difficulty_guidance,
        subject_formatting=subject_formatting,
        units_content=units_content,
        mcq_count=mcq_count,
        frq_count=frq_count
    )
    
    return prompt
