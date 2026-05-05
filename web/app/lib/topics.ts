export interface TopicSuggestion {
  tag: string;
  title: string;
  description: string;
  prompt: string;
  keywords: string[];
  related: string[];
}

interface SuggestionInput {
  answer?: string;
  confidence?: number;
  intent?: string;
  limit?: number;
  question?: string;
}

const TOPIC_CATALOG: Record<string, TopicSuggestion> = {
  about_cvsu: {
    tag: "about_cvsu",
    title: "About CvSU",
    description: "History, background, and university overview",
    prompt: "Tell me about Cavite State University.",
    keywords: ["about cvsu", "history", "overview", "background", "university"],
    related: ["vision_mission", "campus_location", "courses_offered", "contact_info"],
  },
  admissions_exam: {
    tag: "admissions_exam",
    title: "Entrance Exam",
    description: "Exam coverage, schedule, and what to bring",
    prompt: "What should I know about the CvSU entrance exam?",
    keywords: ["entrance exam", "exam", "test", "coverage", "permit"],
    related: ["admissions_requirements", "enrollment_schedule", "contact_info", "tuition_fees"],
  },
  admissions_requirements: {
    tag: "admissions_requirements",
    title: "Admission Requirements",
    description: "Documents, qualifications, and how to apply",
    prompt: "What are the admission requirements at CvSU?",
    keywords: ["admission", "requirements", "application", "apply", "documents", "freshman", "transferee"],
    related: ["admissions_exam", "enrollment_procedure", "tuition_fees", "contact_info"],
  },
  campus_facilities: {
    tag: "campus_facilities",
    title: "Campus Facilities",
    description: "Libraries, labs, student services, and amenities",
    prompt: "What facilities are available at CvSU?",
    keywords: ["facilities", "library", "labs", "amenities", "student services", "campus resources"],
    related: ["campus_location", "student_organizations", "contact_info", "courses_offered"],
  },
  campus_location: {
    tag: "campus_location",
    title: "Campus Location",
    description: "Main campus address, directions, and other campuses",
    prompt: "Where is CvSU located?",
    keywords: ["location", "address", "campus", "directions", "indang"],
    related: ["campus_facilities", "contact_info", "campus_specific", "courses_offered"],
  },
  campus_specific: {
    tag: "campus_specific",
    title: "Campuses",
    description: "Different CvSU campuses and what they offer",
    prompt: "What campuses does CvSU have?",
    keywords: ["campuses", "branches", "imus", "bacoor", "naic", "trece", "indang"],
    related: ["campus_location", "courses_offered", "contact_info", "campus_facilities"],
  },
  contact_info: {
    tag: "contact_info",
    title: "Contact Information",
    description: "Phone numbers, emails, and official channels",
    prompt: "How can I contact CvSU?",
    keywords: ["contact", "phone", "email", "hotline", "office", "registrar", "admissions office"],
    related: ["registrar", "admissions_requirements", "campus_location", "scholarship"],
  },
  courses_offered: {
    tag: "courses_offered",
    title: "Courses and Programs",
    description: "Degree programs, colleges, and study options",
    prompt: "What courses and programs does CvSU offer?",
    keywords: ["courses", "programs", "degree", "college", "major", "curriculum"],
    related: ["admissions_requirements", "tuition_fees", "campus_specific", "contact_info"],
  },
  enrollment_procedure: {
    tag: "enrollment_procedure",
    title: "Enrollment Procedure",
    description: "What happens after admission and how to enroll",
    prompt: "What is the enrollment procedure at CvSU?",
    keywords: ["enrollment", "register", "registration", "cor", "procedure", "advising"],
    related: ["enrollment_schedule", "tuition_fees", "registrar", "contact_info"],
  },
  enrollment_schedule: {
    tag: "enrollment_schedule",
    title: "Enrollment Schedule",
    description: "Important application, exam, and class dates",
    prompt: "What is the CvSU enrollment schedule?",
    keywords: ["schedule", "deadline", "calendar", "semester", "classes begin", "dates"],
    related: ["enrollment_procedure", "admissions_exam", "admissions_requirements", "contact_info"],
  },
  registrar: {
    tag: "registrar",
    title: "Registrar Services",
    description: "TOR, certificates, and student records requests",
    prompt: "What services does the CvSU registrar offer?",
    keywords: ["registrar", "tor", "transcript", "certificate", "records", "documents"],
    related: ["contact_info", "enrollment_procedure", "admissions_requirements", "tuition_fees"],
  },
  scholarship: {
    tag: "scholarship",
    title: "Scholarships",
    description: "Financial aid, TES, merit scholarships, and support",
    prompt: "What scholarships are available at CvSU?",
    keywords: ["scholarship", "financial aid", "tes", "grant", "allowance", "merit"],
    related: ["tuition_fees", "admissions_requirements", "contact_info", "enrollment_procedure"],
  },
  student_organizations: {
    tag: "student_organizations",
    title: "Student Organizations",
    description: "Clubs, student government, and campus activities",
    prompt: "What student organizations are available at CvSU?",
    keywords: ["organizations", "clubs", "student government", "activities", "campus life"],
    related: ["campus_facilities", "about_cvsu", "contact_info", "vision_mission"],
  },
  tuition_fees: {
    tag: "tuition_fees",
    title: "Tuition and Fees",
    description: "Free tuition coverage, misc fees, and payment details",
    prompt: "How much is tuition at CvSU?",
    keywords: ["tuition", "fees", "payment", "free tuition", "ra 10931", "cashier"],
    related: ["scholarship", "enrollment_procedure", "admissions_requirements", "contact_info"],
  },
  vision_mission: {
    tag: "vision_mission",
    title: "Vision and Mission",
    description: "CvSU values, mission, and guiding principles",
    prompt: "What is CvSU's vision and mission?",
    keywords: ["vision", "mission", "motto", "truth excellence service", "values"],
    related: ["about_cvsu", "courses_offered", "student_organizations", "contact_info"],
  },
};

const STARTER_TOPIC_TAGS = [
  "admissions_requirements",
  "courses_offered",
  "tuition_fees",
  "scholarship",
  "campus_location",
  "contact_info",
];

const INTENT_TOPIC_OVERRIDES: Record<string, string[]> = {
  goodbye: STARTER_TOPIC_TAGS,
  greeting: STARTER_TOPIC_TAGS,
  nlu_fallback: STARTER_TOPIC_TAGS,
  thanks: STARTER_TOPIC_TAGS,
};

function normalizeText(text = "") {
  return text
    .toLowerCase()
    .replace(/[_/()-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function addScore(scores: Map<string, number>, tag: string, points: number) {
  if (!TOPIC_CATALOG[tag]) return;
  scores.set(tag, (scores.get(tag) ?? 0) + points);
}

function scoreTopicAgainstText(topic: TopicSuggestion, text: string) {
  const haystack = normalizeText(text);
  if (!haystack) return 0;

  let score = 0;
  const terms = [topic.title, topic.tag, ...topic.keywords];

  for (const term of terms) {
    const needle = normalizeText(term);
    if (!needle || !haystack.includes(needle)) continue;
    score += term === topic.title ? 4 : 2;
  }

  return score;
}

function fallbackFill(tags: string[], limit: number, excludeTag?: string) {
  const filled: string[] = [];

  for (const tag of tags) {
    if (tag === excludeTag || !TOPIC_CATALOG[tag] || filled.includes(tag)) continue;
    filled.push(tag);
    if (filled.length >= limit) break;
  }

  return filled;
}

export function getStarterTopics(limit = 4) {
  return fallbackFill(STARTER_TOPIC_TAGS, limit).map((tag) => TOPIC_CATALOG[tag]);
}

export function getQuickActionTopics() {
  return [
    TOPIC_CATALOG.admissions_requirements,
    TOPIC_CATALOG.tuition_fees,
    TOPIC_CATALOG.courses_offered,
    TOPIC_CATALOG.contact_info,
  ];
}

export function getSuggestionCopy(intent?: string, confidence?: number) {
  if (intent === "nlu_fallback" || (confidence ?? 1) < 0.5) {
    return {
      heading: "Try one of these topics",
      subheading: "These are the closest matches. You can also rephrase your question with more detail.",
    };
  }

  return {
    heading: "Related topics",
    subheading: "Helpful follow-up questions based on the answer above.",
  };
}

export function getSuggestedTopics({
  answer = "",
  confidence,
  intent,
  limit = 4,
  question = "",
}: SuggestionInput) {
  const scores = new Map<string, number>();
  const combinedText = `${question} ${answer}`.trim();
  const intentSeedTags =
    (intent && INTENT_TOPIC_OVERRIDES[intent]) ||
    (intent && TOPIC_CATALOG[intent]?.related) ||
    [];

  for (const topic of Object.values(TOPIC_CATALOG)) {
    const matchScore = scoreTopicAgainstText(topic, combinedText);
    if (matchScore > 0) addScore(scores, topic.tag, matchScore);
  }

  intentSeedTags.forEach((tag, index) => addScore(scores, tag, 12 - index));

  if (!intent || INTENT_TOPIC_OVERRIDES[intent]) {
    STARTER_TOPIC_TAGS.forEach((tag, index) => addScore(scores, tag, 8 - index));
  }

  if (intent === "nlu_fallback" || (confidence ?? 1) < 0.5) {
    STARTER_TOPIC_TAGS.forEach((tag, index) => addScore(scores, tag, 10 - index));
  }

  const excludeTag = intent && TOPIC_CATALOG[intent] ? intent : undefined;
  const rankedTags = [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([tag]) => tag)
    .filter((tag) => tag !== excludeTag);

  const finalTags = [
    ...rankedTags,
    ...fallbackFill(STARTER_TOPIC_TAGS, limit, excludeTag).filter(
      (tag) => !rankedTags.includes(tag),
    ),
  ].slice(0, limit);

  return finalTags.map((tag) => TOPIC_CATALOG[tag]);
}
