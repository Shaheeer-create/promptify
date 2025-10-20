import asyncio
from agents import Agent, Runner, SQLiteSession, set_tracing_disabled
from my_configuration.configuration import model

# Disable tracing for clean execution
set_tracing_disabled(True)

# =========================================================
# 1️⃣ Subject & Composition Agent
# =========================================================
Subject_Composition = Agent(
    name="Subject & Composition Expert",
    instructions=(
        "Analyze the lazy user prompt and enhance subject details: "
        "pose, expression, framing, environment, and composition. "
        "Describe subject naturally (age, gender, ethnicity, clothing) "
        "in professional portrait photography style. Return only refined text."
    ),
    model=model
)
Subject_Composition_as_tool = Subject_Composition.as_tool(
    tool_name="subject_composition_tool",
    tool_description="Enhances subject, pose, framing, and composition."
)

# =========================================================
# 2️⃣ Lighting & Mood Agent
# =========================================================
Lighting_Mood = Agent(
    name="Lighting & Mood Specialist",
    instructions=(
        "Improve lighting and atmosphere based on portrait context. "
        "Add realistic details like soft diffused light, golden hour glow, "
        "or cinematic contrast. Include color temperature and shadows if needed. "
        "Return only refined text."
    ),
    model=model
)
Lighting_Mood_as_tool = Lighting_Mood.as_tool(
    tool_name="lighting_mood_tool",
    tool_description="Enhances lighting, mood, and environmental tone."
)

# =========================================================
# 3️⃣ Camera & Lens Expert
# =========================================================
Camera_Lens = Agent(
    name="Camera & Lens Expert",
    instructions=(
        "Add realistic photography details: camera type, lens focal length, "
        "aperture, and depth of field to create professional portrait realism. "
        "Keep it concise and natural. Return only refined text."
    ),
    model=model
)
Camera_Lens_as_tool = Camera_Lens.as_tool(
    tool_name="camera_lens_tool",
    tool_description="Adds realistic camera and lens details for portraits."
)

# =========================================================
# 4️⃣ Aesthetic & Style Enhancer
# =========================================================
Aesthetic_Style = Agent(
    name="Aesthetic & Style Enhancer",
    instructions=(
        "Enhance the artistic style of the portrait. "
        "Add relevant keywords like 'editorial', 'corporate headshot', "
        "'cinematic look', 'fine art studio lighting', or 'minimalist style'. "
        "Maintain elegance and realism. Return only refined text."
    ),
    model=model
)
Aesthetic_Style_as_tool = Aesthetic_Style.as_tool(
    tool_name="aesthetic_style_tool",
    tool_description="Improves artistic and visual style tone."
)

# =========================================================
# 5️⃣ Technical Quality Enhancer
# =========================================================
Technical_Quality = Agent(
    name="Technical Quality Enhancer",
    instructions=(
        "Add professional rendering attributes: ultra-detailed, "
        "8k resolution, sharp focus, bokeh background, color accuracy. "
        "Avoid repetition and overuse. Keep realistic and balanced. "
        "Return only refined text."
    ),
    model=model
)
Technical_Quality_as_tool = Technical_Quality.as_tool(
    tool_name="technical_quality_tool",
    tool_description="Adds realism, detail, and resolution quality."
)

# =========================================================
# 6️⃣ Style & Genre Agent
# =========================================================
Style_Genre = Agent(
    name="Style & Genre Specialist",
    instructions=(
        "Determine suitable genre or style based on user prompt: "
        "e.g., cinematic, editorial, corporate headshot, fine art. "
        "Add subtle keywords to improve prompt. Return only refined text."
    ),
    model=model
)
Style_Genre_as_tool = Style_Genre.as_tool(
    tool_name="style_genre_tool",
    tool_description="Enhances genre/style keywords for better prompt results."
)

# =========================================================
# 7️⃣ Background & Environment Agent
# =========================================================
Background_Environment = Agent(
    name="Background & Environment Specialist",
    instructions=(
        "Refine environmental context in prompt: "
        "location, setting, props, and background. "
        "Keep realistic and aligned with portrait style. Return only refined text."
    ),
    model=model
)
Background_Environment_as_tool = Background_Environment.as_tool(
    tool_name="background_environment_tool",
    tool_description="Improves background and environmental context."
)

# =========================================================
# 8️⃣ Face Preservation Agent
# =========================================================
Face_Preservation = Agent(
    name="Face Preservation Specialist",
    instructions=(
        "Modify the prompt to enhance image without changing the subject's face. "
        "Ensure facial identity, expression, and features remain intact. "
        "Return only refined text."
    ),
    model=model
)
Face_Preservation_as_tool = Face_Preservation.as_tool(
    tool_name="face_preservation_tool",
    tool_description="Ensures facial features are not altered in the prompt."
)

# =========================================================
# 9️⃣ Final Prompt Assembler
# =========================================================
Final_Assembler = Agent(
    name="Final Prompt Assembler",
    instructions=(
        "Combine all refined outputs into one professional, cohesive prompt. "
        "Ensure natural flow and consistency. Return final prompt only."
    ),
    model=model
)
Final_Assembler_as_tool = Final_Assembler.as_tool(
    tool_name="final_assembler_tool",
    tool_description="Combines all refined components into a final prompt."
)

# =========================================================
# 🎯 Portrait Prompt Enhancer Runner
# =========================================================
PortraitPrompt_Enhancer = Agent(
    name="Portrait Prompt Enhancer",
    instructions="Take lazy portrait prompt and refine it step-by-step using expert agents.",
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

# =========================================================
# 🧠 Run & Print Result
# =========================================================

input_prompt ="make my image like that i have an beautful black car with beautiful background and lighting and the image should be realiand i wear black mafia suit and i am smokimg"

result = Runner.run_sync(
        PortraitPrompt_Enhancer,
        input=input_prompt
    )

print("\n===============================")
print("Final Enhanced Prompt:")
print("===============================")
print(result.final_output)
print("\n")


