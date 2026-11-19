"""
Medical Knowledge Base for MediKiosk RAG
Contains structured clinical profiles across key OPD departments:
General Medicine, Pulmonology, Cardiology, Neurology, Gastroenterology, ENT, Orthopedics.
"""

CLINICAL_DISEASE_PROFILES = [
    {
        "id": "DIS-001",
        "name": "Acute Bronchitis",
        "icd11_code": "CA20.0",
        "snomed_code": "10509002",
        "department": "Pulmonology",
        "hallmark_symptoms": ["cough with or without sputum", "mild fever", "chest wall soreness from coughing", "wheezing", "fatigue"],
        "differentiating_questions": [
            "Is the cough producing green or yellow mucus?",
            "Do you hear a whistling or wheezing sound when breathing?",
            "Have you had chills or severe shortness of breath at rest?"
        ],
        "pertinent_negatives": ["no high persistent fever > 102F", "no pleuritic sharp chest pain", "no hemoptysis (coughing blood)"],
        "red_flags": ["shortness of breath at rest", "hemoptysis", "oxygen saturation < 94%"],
        "typical_duration": "1 to 3 weeks"
    },
    {
        "id": "DIS-002",
        "name": "Pneumonia (Community-Acquired)",
        "icd11_code": "CA40.0",
        "snomed_code": "233604007",
        "department": "Pulmonology",
        "hallmark_symptoms": ["high fever with shaking chills", "productive cough with purulent or rust-colored sputum", "sharp pleuritic chest pain on deep breath", "dyspnea", "tachycardia"],
        "differentiating_questions": [
            "Does the chest pain worsen sharply when you take a deep breath or cough?",
            "Are you experiencing shaking chills (rigors)?",
            "Are you feeling short of breath even while sitting still?"
        ],
        "pertinent_negatives": ["not relieved by bronchodilators alone", "systemic prostration present"],
        "red_flags": ["confusion/altered mental state", "respiratory rate > 30/min", "cyanosis (bluish lips/fingers)"],
        "typical_duration": "Acute (2-5 days onset)"
    },
    {
        "id": "DIS-003",
        "name": "Viral Upper Respiratory Tract Infection (Common Cold / Pharyngitis)",
        "icd11_code": "CA00",
        "snomed_code": "82272006",
        "department": "General Medicine / ENT",
        "hallmark_symptoms": ["runny nose", "nasal congestion", "sore throat", "sneezing", "low-grade fever", "mild dry cough"],
        "differentiating_questions": [
            "Did your symptoms start primarily with a scratchy or sore throat and sneezing?",
            "Do you have a clear watery nasal discharge?",
            "Do you have severe muscle aches or sudden high fever?"
        ],
        "pertinent_negatives": ["no severe shortness of breath", "no focal lung crackles", "no tonsillar exudates with high fever"],
        "red_flags": ["stridor", "difficulty swallowing saliva (drooling)", "inability to open mouth"],
        "typical_duration": "5 to 10 days"
    },
    {
        "id": "DIS-004",
        "name": "Asthma Exacerbation",
        "icd11_code": "CA23.0",
        "snomed_code": "370218001",
        "department": "Pulmonology",
        "hallmark_symptoms": ["episodic wheezing", "dry nighttime cough", "chest tightness", "shortness of breath triggered by allergens/cold/exercise"],
        "differentiating_questions": [
            "Do you have a known history of asthma or allergies?",
            "Is the breathing difficulty worse at night or after physical exertion?",
            "Did symptoms flare up after exposure to cold air, dust, or smoke?"
        ],
        "pertinent_negatives": ["no high fever", "no purulent sputum initially", "responds to inhalers"],
        "red_flags": ["unable to speak full sentences in one breath", "silent chest (no air movement)", "use of accessory neck muscles"],
        "typical_duration": "Episodic flare-up (hours to days)"
    },
    {
        "id": "DIS-005",
        "name": "Acute Coronary Syndrome / Angina Pectoris",
        "icd11_code": "BA41",
        "snomed_code": "22298006",
        "department": "Cardiology",
        "hallmark_symptoms": ["substernal chest pressure or squeezing", "pain radiating to left arm, neck, or jaw", "diaphoresis (profuse cold sweating)", "dyspnea", "nausea"],
        "differentiating_questions": [
            "Does the chest discomfort feel like a heavy weight, squeezing, or burning pressure?",
            "Does the discomfort radiate to your left shoulder, arm, neck, or jaw?",
            "Is it accompanied by sudden cold sweating, lightheadedness, or nausea?"
        ],
        "pertinent_negatives": ["pain is not reproducible by pressing on chest wall", "pain does not change with position or breathing"],
        "red_flags": ["CRITICAL: crushing retrosternal pain > 15 mins", "syncope/fainting", "severe diaphoresis", "hypotension"],
        "typical_duration": "Minutes to hours (EMERGENCY)"
    },
    {
        "id": "DIS-006",
        "name": "Gastroesophageal Reflux Disease (GERD) / Dyspepsia",
        "icd11_code": "DA22",
        "snomed_code": "235595009",
        "department": "Gastroenterology",
        "hallmark_symptoms": ["retrosternal burning (heartburn)", "acid regurgitation into throat", "epigastric discomfort", "worse after spicy/heavy meals or lying down"],
        "differentiating_questions": [
            "Does the burning sensation worsen after meals or when you lie flat?",
            "Do you feel a sour or bitter liquid backing up into your throat?",
            "Does taking antacids or drinking water provide temporary relief?"
        ],
        "pertinent_negatives": ["no radiation to left arm or jaw", "no exertion-induced pain", "no cold sweating"],
        "red_flags": ["dysphagia (difficulty swallowing food)", "vomiting blood (hematemesis)", "unexplained weight loss"],
        "typical_duration": "Chronic / episodic after triggers"
    },
    {
        "id": "DIS-007",
        "name": "Migraine Headache",
        "icd11_code": "8A80",
        "snomed_code": "37796009",
        "department": "Neurology",
        "hallmark_symptoms": ["unilateral throbbing or pulsating head pain", "photophobia (light sensitivity)", "phonophobia (sound sensitivity)", "nausea/vomiting", "visual aura"],
        "differentiating_questions": [
            "Is the pain concentrated mostly on one side of your head?",
            "Does bright light or loud noise aggravate the pain significantly?",
            "Did you see zig-zag lines, flashing lights, or blind spots before the pain started?"
        ],
        "pertinent_negatives": ["no neck stiffness with fever", "no sudden 'thunderclap' onset peaking in seconds"],
        "red_flags": ["sudden worst headache of life (thunderclap)", "fever with stiff neck", "focal weakness or speech slurring"],
        "typical_duration": "4 to 72 hours"
    },
    {
        "id": "DIS-008",
        "name": "Tension-Type Headache",
        "icd11_code": "8A81",
        "snomed_code": "398057008",
        "department": "Neurology",
        "hallmark_symptoms": ["bilateral dull aching pressure", "band-like tightness around forehead or back of head", "neck and shoulder muscle stiffness"],
        "differentiating_questions": [
            "Does the pain feel like a tight band or heavy squeezing around both sides of your head?",
            "Is it associated with prolonged screen time, neck posture, or emotional stress?",
            "Are you free from vomiting, light sensitivity, or visual changes?"
        ],
        "pertinent_negatives": ["no pulsating quality", "no nausea/vomiting", "not aggravated by routine physical activity"],
        "red_flags": ["new onset in patient > 50 years old", "progressive worsening over weeks"],
        "typical_duration": "30 minutes to several days"
    },
    {
        "id": "DIS-009",
        "name": "Acute Gastroenteritis / Food Poisoning",
        "icd11_code": "1A03",
        "snomed_code": "25374005",
        "department": "Gastroenterology",
        "hallmark_symptoms": ["watery diarrhea", "nausea and vomiting", "cramping abdominal pain", "low-grade fever", "dehydration signs"],
        "differentiating_questions": [
            "How many episodes of loose stools or vomiting have you had in the last 24 hours?",
            "Did you eat street food, unpasteurized items, or share meals with someone who got sick?",
            "Is there any blood or black tarry material in your stool or vomit?"
        ],
        "pertinent_negatives": ["no localized right lower quadrant pain with rebound tenderness"],
        "red_flags": ["bloody diarrhea (dysentery)", "signs of severe dehydration (dizziness on standing, no urine > 8h)", "intractable vomiting"],
        "typical_duration": "1 to 5 days"
    },
    {
        "id": "DIS-010",
        "name": "Acute Appendicitis",
        "icd11_code": "DB10.0",
        "snomed_code": "85189001",
        "department": "General Surgery / Emergency",
        "hallmark_symptoms": ["pain starting around navel migrating to right lower quadrant (McBurney's point)", "anorexia", "low fever", "nausea/vomiting after pain starts"],
        "differentiating_questions": [
            "Did the pain start around your belly button and then shift down to the right lower abdomen?",
            "Does the pain worsen when you cough, jump, or press and release the right lower abdomen?",
            "Have you completely lost your appetite since the pain began?"
        ],
        "pertinent_negatives": ["no high diarrhea volume", "pain precedes vomiting (not vice versa)"],
        "red_flags": ["sudden relief followed by diffuse severe abdominal rigidity (perforation)", "high fever with peritoneal signs"],
        "typical_duration": "Progressive over 12-48 hours"
    },
    {
        "id": "DIS-011",
        "name": "Type 2 Diabetes Mellitus (Uncontrolled / Symptomatic)",
        "icd11_code": "5A11",
        "snomed_code": "44054006",
        "department": "Endocrinology / General Medicine",
        "hallmark_symptoms": ["polyuria (excessive urination)", "polydipsia (excessive thirst)", "polyphagia (constant hunger)", "unexplained weight loss", "fatigue", "blurred vision"],
        "differentiating_questions": [
            "Are you waking up multiple times each night specifically to urinate?",
            "Do you feel an unquenchable thirst despite drinking plenty of fluids?",
            "Have you noticed unexplained weight loss or numbness/tingling in your feet?"
        ],
        "pertinent_negatives": ["no fever", "no dysuria or painful urination"],
        "red_flags": ["fruity breath odor", "deep rapid breathing (Kussmaul)", "confusion/lethargy (Diabetic Ketoacidosis / HHS)"],
        "typical_duration": "Weeks to months progressive"
    },
    {
        "id": "DIS-012",
        "name": "Urinary Tract Infection (Cystitis)",
        "icd11_code": "GC08",
        "snomed_code": "68566005",
        "department": "Urology / General Medicine",
        "hallmark_symptoms": ["dysuria (burning urination)", "urinary frequency and urgency", "suprapubic pain", "cloudy or malodorous urine"],
        "differentiating_questions": [
            "Do you feel a burning sensation or stinging when you pass urine?",
            "Do you feel an urgent need to urinate frequently, even if very little comes out?",
            "Do you have high fever, chills, or pain in your lower back / flanks?"
        ],
        "pertinent_negatives": ["no flank pain or costovertebral angle tenderness (rules out pyelonephritis)", "no vaginal/urethral discharge"],
        "red_flags": ["high spiking fever with rigors", "severe flank/kidney pain (acute pyelonephritis)", "inability to pass urine"],
        "typical_duration": "2 to 5 days"
    },
    {
        "id": "DIS-013",
        "name": "Essential Hypertension (Hypertensive Urgency Screen)",
        "icd11_code": "BA00",
        "snomed_code": "59621000",
        "department": "Cardiology / Internal Medicine",
        "hallmark_symptoms": ["occipital morning headache", "dizziness / lightheadedness", "epistaxis (nosebleed)", "visual blurring", "palpitations"],
        "differentiating_questions": [
            "Have you had your blood pressure measured recently?",
            "Do you experience a throbbing headache at the back of your head upon waking?",
            "Are you experiencing chest pressure, shortness of breath, or blurry vision?"
        ],
        "pertinent_negatives": ["often asymptomatic until organ strain occurs"],
        "red_flags": ["BP > 180/120 with chest pain, acute shortness of breath, or neurological deficits (Hypertensive Emergency)"],
        "typical_duration": "Chronic / insidious"
    },
    {
        "id": "DIS-014",
        "name": "Allergic Rhinitis",
        "icd11_code": "CA08.0",
        "snomed_code": "61582004",
        "department": "ENT / Allergy",
        "hallmark_symptoms": ["paroxysmal sneezing", "itchy nose/eyes/palate", "clear rhinorrhea", "nasal congestion", "allergic shiners"],
        "differentiating_questions": [
            "Are your eyes, nose, or the roof of your mouth intensely itchy?",
            "Do symptoms worsen during seasonal changes or exposure to dust, pollen, or pets?",
            "Is the nasal discharge clear and watery without any fever?"
        ],
        "pertinent_negatives": ["no fever", "no purulent thick nasal discharge", "no facial bone tenderness"],
        "red_flags": ["facial swelling", "stridor / wheezing (anaphylaxis warning)"],
        "typical_duration": "Seasonal or perennial"
    },
    {
        "id": "DIS-015",
        "name": "Lumbar Spondylosis / Sciatica (Lumbago)",
        "icd11_code": "FA80",
        "snomed_code": "279039007",
        "department": "Orthopedics / Neurology",
        "hallmark_symptoms": ["lower back pain", "sharp shooting pain radiating down the buttock and back of thigh/calf (sciatica)", "numbness or tingling in foot", "worse with sitting or bending forward"],
        "differentiating_questions": [
            "Does the back pain shoot or radiate down below your knee into your foot or toes?",
            "Do you feel pins-and-needles or numbness in your leg or foot?",
            "Have you experienced any loss of bladder or bowel control, or numbness in the groin/saddle area?"
        ],
        "pertinent_negatives": ["no unexplained fever or weight loss (rules out spinal infection/malignancy)"],
        "red_flags": ["cauda equina syndrome: loss of bowel/bladder control, saddle anesthesia (URGENT SURGERY)"],
        "typical_duration": "Weeks to months, posture-dependent"
    }
]
