"""Practice generation prompt template."""
from typing import Optional
from app.models.course import Unit
from app.models.practice import DifficultyLevel


PRACTICE_PROMPT_TEMPLATE = """
# Role and Objective
You are an **AP Exam Design Expert** and a master of the **Course and Exam Description (CED)** guidelines.
Your task is to design a high-quality **Practice Question Set** for **{course_name}**, covering the following units:
{unit_list}

# Source Material Compliance
1. **Strict CED Alignment:** All questions must align directly with the specific *Learning Objectives* and *Essential Knowledge* outlined below.
2. **Practice Question Style:** The difficulty and style should mimic official AP exam questions.
3. **Difficulty Level:** {difficulty_description}

# Difficulty Setting: {difficulty_level}
{difficulty_guidance}

# Units Content Reference

{units_content}

# Examination Structure

**Section I: Multiple Choice Questions (MCQ)**
* **Quantity:** {mcq_count} questions. YOU MUST GENERATE EXACTLY {mcq_count} MCQ QUESTIONS.
* **Format:**
    * Use **stimulus-based questions** (sets of questions based on a graph, experiment, or text) as much as possible.
    * **CRITICAL FORMATTING:** Each answer option (A), (B), (C), (D) MUST be on its own separate line. Never put multiple options on the same line.
    * **Distractors:** Must be plausible and grounded in common student misconceptions.
* **NO Image Cues:** Generate text-only questions. Do not include any image placeholders or references.
* **Distribution:** Try to distribute questions evenly across the selected units where appropriate.
{saq_section}
**Section II: Free-Response Questions (FRQ)**
* **Quantity:** {frq_count} questions.
* **Type:** Select the specific FRQ types appropriate for this subject (e.g., Long Essay for History, Data Analysis for Science).
* **Task Verbs:** Use official AP task verbs (e.g., Describe, Explain, Identify, Calculate, Justify).
* **IMPORTANT - Document-Based Questions (DBQ):** If generating DBQ questions, you MUST provide the content of all documents with clear labels and source attribution.
* **Distribution:** Try to distribute FRQs across the selected units where appropriate.

# Question Format Examples

**MCQ Example:**
---
**1.**

The excerpt below is from...

Which of the following best describes...?

(A) First option
(B) Second option
(C) Third option
(D) Fourth option
---

**FRQ Example:**
---
**FRQ 1**

(a) **Describe** the main argument...
(b) **Explain** how the evidence supports...
(c) **Evaluate** the extent to which...
---

**DBQ Example (with documents):**
---
**Document-Based Question**

**Documents:**

**Document 1**
Source: Letter from Thomas Jefferson to James Madison, 1787
> "I hold it that a little rebellion now and then is a good thing..."

**Document 2**
Source: Federalist No. 10, James Madison, 1787
> "The latent causes of faction are thus sown in the nature of man..."

**Question:** Using the documents above and your knowledge of United States history, evaluate the extent to which...
---

# Formatting Requirements
1. **Language:** English.
2. **Currency vs Math Formatting:**
   - For **currency** (dollars): Write as plain text (e.g., 8 dollars, 120 dollars) - do NOT wrap currency in LaTeX math delimiters.
   - For **math formulas**: Use LaTeX format enclosed in dollar signs for math expressions only.
3. **Subscripts and Superscripts:**
   - **NEVER use HTML tags** like `<sub>` or `<sup>`. These will NOT render correctly.
   - Use **LaTeX notation** for all subscripts and superscripts, e.g. P_1, Q_M, D_2, x^2, etc.
4. **Layout:** Use clean Markdown formatting. Do NOT use code blocks for regular content.
5. **No Immediate Answers:** Do not put answers directly under the questions. Group all answers at the end.
6. **Complete Output:** You MUST output ALL {mcq_count} MCQ questions with their complete answer explanations.
7. **NO Skill Tags in Output:** Do NOT include skill tags like [Skill: XX] in the generated content. Keep the output clean for students.
8. **CRITICAL - No Self-Correction in Output:**
   - **NEVER** include phrases like "Let me rethink", "Let me reconsider", "Wait, I made a mistake", or any self-correction dialogue.
   - **ONLY output the final, correct answer and explanation.**

# Deliverables (in this order)

1. **Practice Header:**
    * Course name
    * Units covered
    * Difficulty level
    * Question counts

2. **The Questions:**
    * Section I (MCQ) - All {mcq_count} questions.
    {saq_deliverable}* Section II (FRQ) - All {frq_count} questions.
    * **For DBQ:** Include all document excerpts with proper source attribution before the questions.

3. **The Answer Key & Explanations:**
    * **MCQ:** For ALL {mcq_count} questions:
        - Correct answer letter
        - Brief explanation of *why* it is correct and why the distractors are incorrect.
    {saq_answer_deliverable}* **FRQ:**
        * **Model Answer:** A perfect, polished student response.
        * **Scoring Guidelines:** A clear rubric (e.g., "1 point for describing...", "1 point for calculating...").

# Tone
Professional, academic, rigorous, and encouraging.

# Special Instructions
- When writing questions involving calculations, always verify your calculations are correct BEFORE writing.
- Write currency amounts as plain numbers (e.g., "8 dollars", "120 dollars").
- For division/fractions with currency: write "120 / 20 = 6 dollars" using plain text, not LaTeX.

---
**Action:** Please generate the COMPLETE Practice Question Set now. Ensure you include ALL {mcq_count} MCQ questions and {frq_count} FRQ questions with their complete answers.
"""


def get_difficulty_description(difficulty: DifficultyLevel) -> tuple[str, str]:
    """Get difficulty level description and guidance."""
    if difficulty == DifficultyLevel.EASIER:
        return (
            "Easier than AP Exam",
            """- Focus on foundational concepts and straightforward applications
- Use simpler language and shorter stimuli
- Avoid multi-step reasoning questions
- Distractors should be more obviously incorrect
- FRQs should have clearer prompts and require less synthesis"""
        )
    elif difficulty == DifficultyLevel.HARDER:
        return (
            "Harder than AP Exam",
            """- Include more complex, multi-step reasoning questions
- Use longer and more nuanced stimuli
- Require students to synthesize information across multiple concepts
- Distractors should be very plausible and test deeper understanding
- FRQs should require sophisticated analysis and evaluation
- Include questions that connect concepts across different topics"""
        )
    else:  # AP_LEVEL
        return (
            "AP Exam Level",
            """- Match the exact difficulty of official AP exam questions
- Use authentic stimulus materials appropriate for the subject
- Balance between recall, application, and analysis questions
- Distractors should reflect common student misconceptions
- FRQs should match the complexity of actual AP exam FRQs"""
        )


def build_practice_prompt(
    units: list[Unit],
    course_name: str,
    mcq_count: int,
    frq_count: int,
    difficulty: DifficultyLevel,
    skills_dict: dict = None
) -> str:
    """Build the practice generation prompt from unit data.
    
    Args:
        units: List of Unit data
        course_name: Name of the course
        mcq_count: Number of MCQ questions to generate
        frq_count: Number of FRQ questions to generate
        difficulty: Difficulty level
        skills_dict: Dictionary of skills for the course (used internally but not shown in output)
    """
    
    # Build unit list
    unit_list = "\n".join([f"- **Unit {u.unit_number}:** {u.unit_title}" for u in units])
    
    # Get difficulty description and guidance
    difficulty_description, difficulty_guidance = get_difficulty_description(difficulty)
    
    # Check if course needs SAQ section (US History)
    is_history = "history" in course_name.lower()
    saq_section = ""
    saq_deliverable = ""
    saq_answer_deliverable = ""
    
    if is_history and frq_count > 0:
        # For history courses, we might include SAQs as part of FRQ section
        saq_section = """
**Short Answer Questions (SAQ) - Optional for History courses**
* If appropriate for the unit content, include SAQ-style questions with parts (a), (b), (c).
* Include relevant primary source excerpts where appropriate.

"""
    
    # Build units content
    units_content = ""
    for unit in units:
        units_content += f"\n## Unit {unit.unit_number}: {unit.unit_title}\n"
        
        if unit.exam_weight:
            units_content += f"**Exam Weight:** {unit.exam_weight}\n"
        
        # Add unit overview if available
        if unit.unit_overview:
            if unit.unit_overview.summary:
                units_content += f"\n**Overview:**\n{unit.unit_overview.summary}\n"
        
        # Add topics with learning objectives and essential knowledge
        for topic in unit.topics:
            units_content += f"\n### {topic.topic_number}: {topic.topic_title}\n"
            
            if topic.learning_objectives:
                units_content += "\n**Learning Objectives:**\n"
                for lo in topic.learning_objectives:
                    units_content += f"- **{lo.id}:** {lo.summary}\n"
            
            if topic.essential_knowledge:
                units_content += "\n**Essential Knowledge:**\n"
                for ek in topic.essential_knowledge:
                    units_content += f"- **{ek.id}:** {ek.summary}\n"
            
            # Include study guide excerpt if available (truncated)
            if topic.study_guide and isinstance(topic.study_guide, dict):
                content = topic.study_guide.get("content_markdown", "")
                if content:
                    if len(content) > 1500:
                        content = content[:1500] + "..."
                    units_content += f"\n**Study Guide Excerpt:**\n{content}\n"
    
    # Build final prompt
    prompt = PRACTICE_PROMPT_TEMPLATE.format(
        course_name=course_name,
        unit_list=unit_list,
        difficulty_level=difficulty.value.upper().replace("_", " "),
        difficulty_description=difficulty_description,
        difficulty_guidance=difficulty_guidance,
        units_content=units_content,
        mcq_count=mcq_count,
        frq_count=frq_count,
        saq_section=saq_section,
        saq_deliverable=saq_deliverable,
        saq_answer_deliverable=saq_answer_deliverable
    )
    
    return prompt

