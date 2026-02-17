"""
Shared CV profile configuration & smart filtering engine.
Single source of truth for all spiders' keyword filtering.

Based on: Ahmed Sakr - CGI Artist & Digital Product Designer

How it works:
  - SEARCH_KEYWORDS: What to search for on job sites (titles)
  - RELEVANT_KEYWORDS: Broad match for filtering results (regex word boundaries)
  - TITLE_PATTERNS: Exact job titles you want (high relevance)
  - NEGATIVE_KEYWORDS: Titles to skip (e.g. "Waiter" matches "AI" but is irrelevant)
  - score_job(): Returns 0-100 relevance score for any job item
  - is_relevant(): Quick boolean check (used by spiders)
"""

import re

# ═══════════════════════════════════════════════════════════════════════════
# PROFILE - Your identity (used for scoring)
# ═══════════════════════════════════════════════════════════════════════════

PROFILE = {
    'name': 'Ahmed Sakr',
    'title': 'CGI Artist & Digital Product Designer',
    'years_experience': 8,
    'languages': ['English', 'Arabic'],
    'locations_preferred': ['Remote', 'Egypt', 'Saudi Arabia', 'UAE', 'Qatar', 'Kuwait', 'Europe', 'Germany'],
}

# ═══════════════════════════════════════════════════════════════════════════
# SEARCH KEYWORDS - What to type into search boxes on job sites
# ═══════════════════════════════════════════════════════════════════════════

SEARCH_KEYWORDS = [
    # Primary roles (most relevant)
    "Product Designer",
    "3D Artist",
    "CGI Artist",
    "Digital Product Designer",
    "UI UX Designer",
    "Motion Designer",
    "Motion Graphics Designer",
    "Art Director",
    "Creative Director",

    # Specialized
    "Generative AI Designer",
    "Blender Artist",
    "Unreal Engine Artist",
    "VFX Artist",
    "3D Visualizer",

    # Broader (still relevant)
    "Graphic Designer",
    "Visual Designer",
    "Senior Designer",
]

# Arabic search queries (for Arabic platforms)
SEARCH_KEYWORDS_AR = [
    "مصمم منتجات رقمية",
    "مصمم ثلاثي الابعاد",
    "مصمم جرافيك",
    "مصمم UI UX",
    "مصمم موشن جرافيك",
    "فنان CGI",
    "مدير فني",
    "مدير ابداعي",
]

# ═══════════════════════════════════════════════════════════════════════════
# RELEVANT KEYWORDS - Broad regex filters (used by all spiders)
# Any job title/description containing these passes initial filter
# ═══════════════════════════════════════════════════════════════════════════

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

# Arabic keyword patterns (for social media & MENA platforms)
RELEVANT_KEYWORDS_AR = [
    r'مصمم', r'ديزاينر', r'فنان', r'مدير فني', r'مدير ابداعي',
    r'ثلاثي', r'ثري دي', r'جرافيك', r'موشن', r'تصميم',
    r'واجهة', r'رندر', r'بلندر', r'انريل', r'فيجما',
    r'مونتاج', r'انيميشن', r'VFX', r'CGI',
]

# ═══════════════════════════════════════════════════════════════════════════
# TITLE PATTERNS - Exact job titles (HIGH relevance, +35 score)
# ═══════════════════════════════════════════════════════════════════════════

TITLE_PATTERNS = [
    # Perfect match roles
    r'(?:Senior\s+)?Product\s+Designer',
    r'(?:Senior\s+)?3D\s+Artist',
    r'(?:Senior\s+)?CGI\s+Artist',
    r'(?:Senior\s+)?UI/?UX\s+Designer',
    r'(?:Senior\s+)?Motion\s+(?:Graphics?\s+)?Designer',
    r'(?:Senior\s+)?Art\s+Director',
    r'(?:Senior\s+)?Creative\s+Director',
    r'(?:Senior\s+)?Visual\s+Designer',
    r'(?:Senior\s+)?Digital\s+(?:Product\s+)?Designer',
    r'(?:Senior\s+)?Graphic\s+Designer',
    r'Generative\s+AI\s+Designer',
    r'VFX\s+Artist',
    r'3D\s+Visualizer',
    r'Blender\s+Artist',
    r'Unreal\s+(?:Engine\s+)?(?:Artist|Developer|Designer)',
    # Arabic titles
    r'مصمم\s+منتجات',
    r'مصمم\s+جرافيك',
    r'مصمم\s+ثلاثي',
    r'فنان\s+CGI',
    r'مدير\s+فني',
    r'مدير\s+ابداعي',
]

# ═══════════════════════════════════════════════════════════════════════════
# NEGATIVE KEYWORDS - Skip these even if they match broad filters
# (e.g. "Waiter" contains "AI", "Sustainability" contains "AI")
# ═══════════════════════════════════════════════════════════════════════════

NEGATIVE_KEYWORDS = [
    # Irrelevant job titles
    r'\bWaiter\b', r'\bWaitress\b', r'\bChef\b', r'\bCook\b',
    r'\bDriver\b', r'\bCleaner\b', r'\bSecurity\s+Guard\b',
    r'\bAccountant\b', r'\bNurse\b', r'\bDoctor\b', r'\bPharmacist\b',
    r'\bTeacher\b', r'\bProfessor\b', r'\bLecturer\b',
    r'\bMechanic\b', r'\bElectrician\b', r'\bPlumber\b',
    r'\bSales\s+(?:Rep|Executive|Agent)\b',
    r'\bCall\s+Center\b', r'\bCustomer\s+Service\b',
    r'\bData\s+Entry\b', r'\bReceptionist\b',
    r'\bHR\s+(?:Manager|Specialist|Officer)\b',
    r'\bLawyer\b', r'\bLegal\b',
    r'\bSustainability\b',
    # News / PR / blog post indicators (not job listings)
    r'\bannounces\b', r'\blaunches\b', r'\bwins\s+award\b',
    r'\bpartners\s+with\b', r'\bquarterly\s+results\b',
    r'\bpress\s+release\b', r'\bour\s+journey\b',
    r'\bwe\s+are\s+proud\b', r'\bin\s+the\s+news\b',
    r'\bcompany\s+update\b', r'\breported\s+revenue\b',
    r'\bacquires\b', r'\braises\s+\$', r'\bIPO\b',
]

# ═══════════════════════════════════════════════════════════════════════════
# TOOL & SKILL KEYWORDS - Bonus score for matching tools from CV
# ═══════════════════════════════════════════════════════════════════════════

TOOL_KEYWORDS = [
    r'Blender', r'Unreal\s*Engine', r'Figma', r'Cinema\s*4D', r'C4D',
    r'After\s*Effects', r'Photoshop', r'Illustrator', r'Premiere',
    r'Substance', r'ZBrush', r'Maya', r'Houdini',
    r'Midjourney', r'Stable\s*Diffusion', r'DALL[-\s]?E', r'ComfyUI',
    r'Three\.?js', r'WebGL', r'React', r'Next\.?js',
    r'DaVinci', r'Nuke',
]

# ═══════════════════════════════════════════════════════════════════════════
# LOCATION SCORING - Preferred locations get bonus points
# ═══════════════════════════════════════════════════════════════════════════

LOCATION_SCORES = {
    'remote': 20,
    'egypt': 15, 'cairo': 15, 'alexandria': 10,
    'saudi': 15, 'riyadh': 15, 'jeddah': 12, 'neom': 18, 'ksa': 15,
    'uae': 12, 'dubai': 12, 'abu dhabi': 10,
    'qatar': 8, 'doha': 8,
    'kuwait': 8,
    'germany': 10, 'berlin': 10,
    'europe': 8, 'uk': 8, 'netherlands': 8,
    # Arabic locations
    'عن بعد': 20, 'ريموت': 20,
    'مصر': 15, 'القاهرة': 15,
    'السعودية': 15, 'الرياض': 15, 'جدة': 12,
    'الامارات': 12, 'دبي': 12,
}

# Freelance-specific extras (broader for gig platforms)
FREELANCE_EXTRA_KEYWORDS = [
    r'Logo', r'Video', r'Render', r'Model',
]


# ═══════════════════════════════════════════════════════════════════════════
# SCORING ENGINE - Pre-compiled patterns (built once, used many times)
# ═══════════════════════════════════════════════════════════════════════════

_relevant_pattern = re.compile(
    r'\b(' + '|'.join(RELEVANT_KEYWORDS) + r')\b', re.IGNORECASE
)
_relevant_ar_pattern = re.compile(
    '(' + '|'.join(RELEVANT_KEYWORDS_AR) + ')', re.IGNORECASE
)
_title_pattern = re.compile(
    '(' + '|'.join(TITLE_PATTERNS) + ')', re.IGNORECASE
)
_negative_pattern = re.compile(
    '(' + '|'.join(NEGATIVE_KEYWORDS) + ')', re.IGNORECASE
)
_tool_pattern = re.compile(
    r'\b(' + '|'.join(TOOL_KEYWORDS) + r')\b', re.IGNORECASE
)


def score_job(title='', description='', location='', job_type=''):
    """
    Score a job's relevance to Ahmed's CV profile (0-100).

    0 = irrelevant (negative keyword hit)
    1-29 = weak match
    30-59 = good match
    60-100 = excellent match
    """
    score = 0
    text = f"{title} {description}"

    # NEGATIVE CHECK - instant disqualify
    if _negative_pattern.search(title):
        return 0

    # TITLE MATCH - exact role match is most valuable
    if _title_pattern.search(title):
        score += 35

    # RELEVANT KEYWORDS in title (broad match)
    title_matches = _relevant_pattern.findall(title)
    score += min(len(title_matches) * 8, 24)

    # RELEVANT KEYWORDS in description
    if description:
        desc_matches = _relevant_pattern.findall(description)
        score += min(len(desc_matches) * 2, 10)

    # ARABIC keyword match
    if _relevant_ar_pattern.search(text):
        score += 5

    # TOOL MATCH - specific tools from CV
    tool_matches = _tool_pattern.findall(text)
    score += min(len(tool_matches) * 5, 15)

    # LOCATION SCORE
    location_text = f"{location} {job_type}".lower()
    location_bonus = 0
    for loc_key, loc_score in LOCATION_SCORES.items():
        if loc_key in location_text:
            location_bonus = max(location_bonus, loc_score)
    score += location_bonus

    return min(score, 100)


def is_relevant(title='', description=''):
    """
    Quick boolean: does this job match Ahmed's CV at all?
    Used by spiders for initial filtering.
    """
    if _negative_pattern.search(title):
        return False

    if _relevant_pattern.search(title):
        return True

    if description and _relevant_pattern.search(description):
        return True

    text = f"{title} {description}"
    if _relevant_ar_pattern.search(text):
        return True

    return False


def is_relevant_social(text):
    """
    Relevance check for social media posts (Twitter, Reddit, Facebook, Telegram).
    Requires EITHER a specific role keyword OR a broad keyword + hiring indicator.
    This avoids false positives like "Buy this amazing product now!"
    """
    if not text or len(text) < 15:
        return False

    # Arabic keywords always relevant (very specific to job context)
    if _relevant_ar_pattern.search(text):
        return True

    # Specific keywords that are always relevant (unlikely to be spam)
    _specific = re.compile(
        r'\b(Designer|Artist|3D|CGI|VFX|Blender|Unreal|Figma|'
        r'Art Director|Creative Director|Motion Graphics|UI/?UX|'
        r'DOOH|Anamorphic|Generative AI)\b', re.IGNORECASE
    )
    if _specific.search(text):
        return True

    # Broad keywords (Product, AI, Web, Digital, Creative, Animation)
    # need a hiring indicator to be relevant
    if _relevant_pattern.search(text):
        _hiring = re.compile(
            r'\b(hiring|looking for|seeking|wanted|job|position|'
            r'opening|role|apply|join|opportunity|remote|freelance|'
            r'مطلوب|وظيفة|توظيف|نبحث)\b', re.IGNORECASE
        )
        if _hiring.search(text):
            return True

    return False
