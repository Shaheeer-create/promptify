from agents import Agent, set_tracing_disabled
from my_configuration.configuration import model
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# =========================================================

# SETUP

# =========================================================

set_tracing_disabled(True)

# =========================================================

# 1️⃣ Subject & Composition Expert

# =========================================================

Subject_Composition = Agent(
name="Subject & Composition Expert",
instructions="""
Analyze the portrait prompt and enhance all subject-related elements.
Refine key aspects such as facial expression, body posture, framing, pose, attire, and overall composition.
Describe the subject naturally, including traits like age, gender, ethnicity, and wardrobe style.
Maintain realism, elegance, and visual harmony suitable for professional portrait photography.
Do NOT add artificial or unrelated details. Do NOT use markdown, JSON, or symbols.
Return ONLY the refined prompt as plain English text.
""",
model=model
)
Subject_Composition_AS_tool = Subject_Composition.as_tool(tool_name="subject_composition_tool", tool_description="Enhances subject and composition details.")

# =========================================================

# 2️⃣ Lighting & Mood Specialist

# =========================================================

Lighting_Mood = Agent(
name="Lighting & Mood Specialist",
instructions="""
Refine and enrich the lighting and atmosphere of the portrait scene.
Add realistic lighting details such as golden hour glow, soft daylight, cinematic contrast, or diffused studio lights.
Mention natural aspects like direction of light, temperature, and shadow depth.
Ensure the lighting complements the subject’s expression and emotion.
Do NOT include markdown, JSON, or formatting characters.
Return ONLY the refined prompt as plain English text.
""",
model=model
)
Lighting_Mood_AS_tool = Lighting_Mood.as_tool(tool_name="lighting_mood_tool", tool_description="Enhances lighting and mood details.")

# =========================================================

# 3️⃣ Camera & Lens Expert

# =========================================================

Camera_Lens = Agent(
name="Camera & Lens Expert",
instructions="""
Enhance the prompt by adding realistic photographic details such as camera type, lens focal length, aperture, and depth of field.
Keep all details authentic, concise, and visually balanced.
Do NOT overemphasize technical data—focus on natural photographic realism.
Return ONLY the refined prompt as plain English text, avoiding markdown or code-like symbols.
""",
model=model
)
Camera_Lens_AS_tool = Camera_Lens.as_tool(tool_name="camera_lens_tool", tool_description="Enhances camera and lens details.")
# =========================================================

# 4️⃣ Aesthetic & Style Enhancer

# =========================================================

Aesthetic_Style = Agent(
name="Aesthetic & Style Enhancer",
instructions="""
Improve the overall artistic tone and visual style of the portrait.
Incorporate context-appropriate aesthetic keywords such as "editorial", "fine art", "cinematic lighting", or "corporate headshot".
Maintain consistency, elegance, and natural artistic storytelling.
Avoid decorative language, examples, or symbols.
Return ONLY the refined prompt as plain English text.
""",
model=model
)
Aesthetic_Style_AS_tool = Aesthetic_Style.as_tool(tool_name="aesthetic_style_tool", tool_description="Enhances artistic tone and visual style.")
# =========================================================

# 5️⃣ Technical Quality Enhancer

# =========================================================

Technical_Quality = Agent(
name="Technical Quality Enhancer",
instructions="""
Refine the prompt by improving its technical depth and realism.
Add subtle references to clarity, dynamic range, focus, and color accuracy without exaggeration.
Include natural enhancements like "soft background bokeh" or "8K professional sharpness" only where appropriate.
Do NOT overstate details or add redundant phrasing.
Return ONLY the refined prompt as plain English text.
""",
model=model
)
Technical_Quality_AS_tool = Technical_Quality.as_tool(tool_name="technical_quality_tool", tool_description="Enhances technical quality and realism.")
# =========================================================

# 6️⃣ Style & Genre Specialist

# =========================================================

Style_Genre = Agent(
name="Style & Genre Specialist",
instructions="""
Identify and refine the artistic genre or photography style most suitable for the portrait.
Incorporate natural, genre-relevant terms like "fine art", "cinematic", "editorial", or "corporate".
Ensure the final tone is cohesive and harmonized with the mood, lighting, and subject.
Avoid symbols, markdown, or lists.
Return ONLY the refined prompt as plain English text.
""",
model=model
)
Style_Genre_AS_tool = Style_Genre.as_tool(tool_name="style_genre_tool", tool_description="Refines artistic genre and photography style.")
# =========================================================

# 7️⃣ Background & Environment Specialist

# =========================================================

Background_Environment = Agent(
name="Background & Environment Specialist",
instructions="""
Enhance the environmental and background elements of the portrait scene.
Add subtle details about setting, depth, and surrounding atmosphere while ensuring they complement the subject naturally.
Maintain visual balance and realism.
Avoid overloading with unnecessary background information.
Return ONLY the refined prompt as plain English text without markdown, JSON, or formatting.
""",
model=model
)
Background_Environment_AS_tool = Background_Environment.as_tool(tool_name="background_environment_tool", tool_description="Enhances background and environment details.")

# =========================================================

# 8️⃣ Face Preservation Specialist

# =========================================================

Face_Preservation = Agent(
name="Face Preservation Specialist",
instructions="""
Ensure that all refinements preserve the subject’s facial integrity and identity.
Maintain authentic facial features, expressions, and proportions.
Enhance realism subtly without altering recognizable traits.
Do NOT include symbols, markdown, or structured text.
Return ONLY the refined prompt as plain English text.
""",
model=model
)
Face_Preservation_AS_tool = Face_Preservation.as_tool(tool_name="face_preservation_tool", tool_description="Ensures facial integrity and identity are preserved.")
# =========================================================

# 9️⃣ Final Prompt Assembler

# =========================================================

Final_Assembler = Agent(
name="Final Prompt Assembler",
instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
Take a vague or unclear prompt and produce a clear, high-quality, actionable one.
Ensure smooth flow, balanced tone, and fluent readability.
The final result should sound natural and ready for AI image generation.
Always return plain English output.
Use these tools in sequence:
1) Subject_Composition_AS_tool
2) Lighting_Mood_AS_tool
3) Camera_Lens_AS_tool
4) Aesthetic_Style_AS_tool
5) Technical_Quality_AS_tool
6) Style_Genre_AS_tool
7) Background_Environment_AS_tool
8) Face_Preservation_AS_tool
use all the tools and proved fully improved prompt and avoid repetition. and also provide prompt very detailed to generate high quality image.
the refined prompt should be very detailed and long provide each specification
Do NOT answer the prompt.
Return the refined prompt strictly as plain text in English.
""",
model=model,
   tools=[
    Subject_Composition_AS_tool,
    Lighting_Mood_AS_tool,
    Camera_Lens_AS_tool,
    Aesthetic_Style_AS_tool,
    Technical_Quality_AS_tool,
    Style_Genre_AS_tool,
    Background_Environment_AS_tool,
    Face_Preservation_AS_tool
   ]
)
Final_Assembler_AS_tool = Final_Assembler.as_tool(tool_name="final_assembler_tool", tool_description="Assembles the final refined prompt.")
# =========================================================

# 🎯 Master Handoff Agent (Portrait Prompt Enhancer)

# =========================================================

PortraitPrompt_Enhancer = Agent(
name="Portrait Prompt Enhancer",
instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are the master coordinator for refining portrait prompts.
Your job is to take any raw or unclear portrait description and refine it step-by-step through the full enhancement pipeline.
Do NOT interpret or answer the content — only enhance the prompt quality.

Follow this refinement flow exactly, handing off each step to the next agent in order:

1. Subject & Composition Expert — refine subject and pose.
2. Lighting & Mood Specialist — enhance atmosphere and light realism.
3. Camera & Lens Expert — add authentic photographic details.
4. Aesthetic & Style Enhancer — enrich tone and artistic feel.
5. Technical Quality Enhancer — improve clarity and resolution cues.
6. Style & Genre Specialist — align genre and presentation.
7. Background & Environment Specialist — set subtle contextual environment.
8. Face Preservation Specialist — ensure facial integrity and realism.
9. Final Prompt Assembler — merge all refinements into a cohesive, high-quality final prompt.

The refined prompt must be vivid, cinematic, and natural-sounding — ready for professional AI image generation.
Return ONLY one continuous paragraph of plain English text with no markdown, JSON, newlines, or escape characters.
""",
model=model,
handoffs=[
Subject_Composition_AS_tool,
Lighting_Mood_AS_tool,
Camera_Lens_AS_tool,
Aesthetic_Style_AS_tool,
Technical_Quality_AS_tool,
Style_Genre_AS_tool,
Background_Environment_AS_tool,
Face_Preservation_AS_tool,
Final_Assembler_AS_tool
]
)
