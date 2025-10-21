from agents import Agent,set_tracing_disabled
from my_configuration.configuration import model


# Disable tracing for clean execution
set_tracing_disabled(True)
USER_ID = "user123"
# =========================================================
# 1️⃣ Subject & Composition Agent
# =========================================================
Subject_Composition = Agent(
    name="Subject & Composition Expert",
    instructions=(
        "Analyze the given portrait prompt and enhance all subject-related details. "
        "Refine aspects such as pose, expression, framing, body position, attire, and environment composition. "
        "Describe the subject naturally, including relevant traits like age, gender, ethnicity, and clothing style. "
        "Ensure the description feels authentic, elegant, and visually balanced — suitable for professional portrait photography. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Subject_Composition_as_tool = Subject_Composition.as_tool(
    tool_name="subject_composition_tool",
    tool_description="Enhances subject, pose, expression, framing, and composition realism."
)

# =========================================================
# 2️⃣ Lighting & Mood Agent
# =========================================================
Lighting_Mood = Agent(
    name="Lighting & Mood Specialist",
    instructions=(
        "Refine the lighting, atmosphere, and overall mood of the portrait prompt. "
        "Incorporate realistic lighting details such as soft daylight, cinematic contrast, golden hour tones, or studio lighting setups. "
        "Mention light direction, color temperature, and shadows naturally where relevant to enhance visual depth. "
        "Ensure the tone matches the portrait’s intended emotion and aesthetic. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Lighting_Mood_as_tool = Lighting_Mood.as_tool(
    tool_name="lighting_mood_tool",
    tool_description="Improves lighting, mood, and environmental atmosphere."
)

# =========================================================
# 3️⃣ Camera & Lens Expert
# =========================================================
Camera_Lens = Agent(
    name="Camera & Lens Expert",
    instructions=(
        "Add realistic photography specifications to the prompt such as camera type, lens focal length, aperture, "
        "and depth of field to achieve professional realism. "
        "Keep these details concise, accurate, and natural, ensuring they complement rather than overwhelm the scene. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Camera_Lens_as_tool = Camera_Lens.as_tool(
    tool_name="camera_lens_tool",
    tool_description="Adds authentic camera and lens details for realistic portraits."
)

# =========================================================
# 4️⃣ Aesthetic & Style Enhancer
# =========================================================
Aesthetic_Style = Agent(
    name="Aesthetic & Style Enhancer",
    instructions=(
        "Refine the artistic tone and visual style of the portrait. "
        "Incorporate relevant aesthetic keywords such as 'editorial', 'corporate headshot', 'cinematic lighting', or 'fine art studio'. "
        "Maintain elegance, cohesion, and realism throughout the prompt while enhancing visual storytelling. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Aesthetic_Style_as_tool = Aesthetic_Style.as_tool(
    tool_name="aesthetic_style_tool",
    tool_description="Improves artistic tone and portrait visual style."
)

# =========================================================
# 5️⃣ Technical Quality Enhancer
# =========================================================
Technical_Quality = Agent(
    name="Technical Quality Enhancer",
    instructions=(
        "Add professional rendering attributes that enhance technical realism — for example: ultra-detailed textures, "
        "8K resolution clarity, balanced sharpness, soft background bokeh, and accurate color reproduction. "
        "Ensure the improvements sound natural, not exaggerated, and fit the overall portrait context. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Technical_Quality_as_tool = Technical_Quality.as_tool(
    tool_name="technical_quality_tool",
    tool_description="Improves rendering realism, resolution, and professional clarity."
)

# =========================================================
# 6️⃣ Style & Genre Agent
# =========================================================
Style_Genre = Agent(
    name="Style & Genre Specialist",
    instructions=(
        "Determine and apply the most appropriate artistic genre or photography style based on the prompt’s tone and content. "
        "Use subtle, context-appropriate keywords like 'cinematic', 'fine art', 'corporate', or 'editorial look'. "
        "Keep the style cohesive with the intended mood and subject presentation. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Style_Genre_as_tool = Style_Genre.as_tool(
    tool_name="style_genre_tool",
    tool_description="Adds suitable genre and style keywords to enrich portrait tone."
)

# =========================================================
# 7️⃣ Background & Environment Agent
# =========================================================
Background_Environment = Agent(
    name="Background & Environment Specialist",
    instructions=(
        "Enhance the environmental and background elements of the prompt. "
        "Include realistic details about the setting, location, and props while keeping them aligned with the portrait’s subject and style. "
        "Ensure background complements rather than distracts, maintaining visual harmony. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Background_Environment_as_tool = Background_Environment.as_tool(
    tool_name="background_environment_tool",
    tool_description="Refines environmental context and background setting."
)

# =========================================================
# 8️⃣ Face Preservation Agent
# =========================================================
Face_Preservation = Agent(
    name="Face Preservation Specialist",
    instructions=(
        "Ensure the subject’s facial identity, expression, and natural features remain unchanged during enhancement. "
        "Refine the prompt to improve realism without altering recognizable facial characteristics. "
        "Focus on maintaining authenticity and subtle enhancement only. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Face_Preservation_as_tool = Face_Preservation.as_tool(
    tool_name="face_preservation_tool",
    tool_description="Preserves facial integrity while enhancing the image."
)

# =========================================================
# 9️⃣ Final Prompt Assembler
# =========================================================
Final_Assembler = Agent(
    name="Final Prompt Assembler",
    instructions=(
        "Combine all refined outputs from the specialized agents into one cohesive, professional, and fluent final prompt. "
        "Ensure smooth phrasing, logical flow, and consistent tone across all elements. "
        "The result should feel like a polished photography prompt ready for AI generation. "
        "Return ONLY the refined prompt as plain text in English — no JSON, markdown, or examples."
    ),
    model=model
)
Final_Assembler_as_tool = Final_Assembler.as_tool(
    tool_name="final_assembler_tool",
    tool_description="Merges all refined components into a single professional prompt."
)

# =========================================================
# 🎯 Portrait Prompt Enhancer Runner
# =========================================================
PortraitPrompt_Enhancer = Agent(
    name="Portrait Prompt Enhancer",
    instructions="Take a rough or lazy portrait prompt and refine it step-by-step using all expert agents to produce a polished final photography prompt.",
    model=model,
    tools=[
        Subject_Composition_as_tool,
        Lighting_Mood_as_tool,
        Camera_Lens_as_tool,
        Aesthetic_Style_as_tool,
        Technical_Quality_as_tool,
        Style_Genre_as_tool,
        Background_Environment_as_tool,
        Face_Preservation_as_tool,
        Final_Assembler_as_tool
    ]
)

