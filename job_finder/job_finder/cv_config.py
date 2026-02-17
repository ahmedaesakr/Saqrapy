"""
Shared CV profile configuration.
Single source of truth for all spiders' keyword filtering.
Based on: Ahmed Sakr - CGI Artist & Digital Product Designer
"""

# Keywords that match CV skills and target roles
# Used by all spiders for title/description filtering
RELEVANT_KEYWORDS = [
    # Core Roles
    r'Designer', r'Artist', r'Art Director', r'Creative Director',
    # 3D & CGI
    r'3D', r'CGI', r'VFX', r'Visualizer',
    # Product & UX
    r'Product', r'UI', r'UX',
    # Motion & Video
    r'Motion', r'Animation',
    # Tools (from CV)
    r'Unreal', r'Blender', r'Figma',
    # AI & Tech
    r'Generative', r'AI', r'Graphic',
    # Web & Dev
    r'Creative', r'Frontend', r'Web', r'Digital',
    # Specialty (from CV)
    r'DOOH', r'Anamorphic',
]

# Search queries used by job board spiders
SEARCH_KEYWORDS = [
    "Product Designer",
    "3D Artist",
    "CGI Artist",
    "Digital Product Designer",
    "UI UX Designer",
    "Motion Designer",
    "Motion Graphics",
    "Generative AI",
    "Generative AI Designer",
    "Blender Artist",
    "Unreal Engine",
    "Art Director",
    "Creative Director",
]

# Freelance-specific extras (broader for gig platforms)
FREELANCE_EXTRA_KEYWORDS = [
    r'Logo', r'Video', r'Render', r'Model',
]
