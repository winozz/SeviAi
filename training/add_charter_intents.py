"""Add intents sourced from CvSU Citizen's Charter 2026.

Source pages cited inline. Existing intents are kept; new tags are appended
to data/cavsu_intents.json and models/responses_map.json. After running this,
execute `python training/train_hybrid.py` and restart the API.
"""
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTENTS_PATH = ROOT / "data" / "cavsu_intents.json"
RESPONSES_PATH = ROOT / "models" / "responses_map.json"

# ----------------------------------------------------------------------
# New intents — each sourced from a specific Citizen's Charter procedure.
# Patterns mix English, Filipino, and code-switched phrasings to match
# how students actually ask (informed by chat_*.log inspection).
# ----------------------------------------------------------------------

NEW_INTENTS = [
    {
        "tag": "student_refund",
        "patterns": [
            "How do I get a tuition refund?",
            "How to apply for refund at CvSU?",
            "I want to claim my refund",
            "where do I file student refund",
            "Student Refund Form how to get",
            "may refund ba ang CvSU",
            "Paano mag-refund ng tuition?",
            "Saan ako mag-apply para sa refund?",
            "I overpaid my tuition can I get refund",
            "refund of overpayment",
            "process for student refund",
            "how long does refund take",
            "may chance ba na ma-refund yung bayad ko",
            "I dropped a class, can I get a refund?",
            "tuition refund procedure",
            "where do I claim my refund check",
        ],
        "responses": [
            "STUDENT REFUND (Accounting Office):\n\n1. Get the Application for Refund Form from the Accounting Office.\n2. Fill out and submit with required supporting documents (varies by nature of refund).\n3. Accounting verifies completeness and stamps received.\n4. Refund payroll is prepared after the cut-off date of the allowable refund period.\n\nWHO MAY AVAIL: All students.\nFEES: None.\nPROCESSING TIME: ~2 days and 22 minutes total.\nSource: CvSU Citizen's Charter 2026 — Accounting Office, p.148.",
            "Para mag-apply ng refund: kunin ang Application for Refund Form sa Accounting Office, sagutan at isumite kasama ng requirements. I-pa-verify, at maghihintay ng cutoff date para sa refund payroll. Walang bayad. Karaniwang umaabot ng 2 days at 22 minutes ang buong proseso. (Citizen's Charter 2026, p.148)",
        ],
    },
    {
        "tag": "student_clearance_signing",
        "patterns": [
            "How do I get my clearance signed?",
            "where to sign student clearance",
            "Student Clearance Form how to process",
            "how to process clearance at CvSU",
            "paano mag-pa-clear sa Accounting?",
            "saan ko ipapasigna ang clearance ko?",
            "how long to sign clearance",
            "do I need to pay for clearance",
            "Accounting signing of clearance",
            "I need my clearance signed for graduation",
            "clearance process CvSU",
            "Accounting office clearance",
            "may bayad ba ang pagpapa-clear ng student clearance",
            "where do I get Student Clearance Form",
            "step by step clearance signing",
        ],
        "responses": [
            "STUDENT CLEARANCE — Accounting Office signing:\n\n1. Get the Student Clearance Form from the College Registrar.\n2. Present it at the Accounting Office.\n3. Staff checks Student Account Assessment System for any balance.\n4. If clear, the form is signed and returned to you.\n\nFEES: None.\nPROCESSING TIME: ~5 minutes.\nSource: CvSU Citizen's Charter 2026 — Accounting Office, p.147.",
            "Para mag-pa-sign ng clearance sa Accounting: kunin muna ang Student Clearance Form sa College Registrar, dalhin sa Accounting Office, i-check nila kung may balance ka. Kung wala, papipirmahan agad. Libre at 5 minutes lang. (Citizen's Charter 2026, p.147)",
        ],
    },
    {
        "tag": "foreign_student_admission",
        "patterns": [
            "How can a foreign student apply at CvSU?",
            "foreign student admission process",
            "I am from another country can I apply",
            "international student requirements CvSU",
            "do you accept foreign students",
            "how much is the testing fee for foreign students",
            "foreign applicant requirements",
            "what documents do I need as a foreign student",
            "I need student visa to study at CvSU",
            "process for non-Filipino applicants",
            "I'm Indonesian and want to apply, how do I do that?",
            "OSAS foreign student application",
            "is interview required for foreign students",
            "Police Clearance from country of origin",
            "Affidavit of financial support",
        ],
        "responses": [
            "FOREIGN STUDENT ADMISSION (OSAS):\n\nREQUIREMENTS:\n- Accomplished Application Form for Admission (download at www.cvsu.edu.ph)\n- Photocopy of Report Card / Transcript of Records\n- Photocopy of transfer credentials\n- Photocopy of student visa (passport)\n- Police Clearance from country of origin\n- Authenticated Affidavit of Financial Support\n- 2 pcs 1x1 photo (white background)\n- 1 short ordinary folder\n- Official receipt for testing fee\n\nFEE: PHP 500 (testing fee, paid at Cashier's Office).\nPROCESS:\n1. Pay testing fee at Cashier's Office.\n2. Submit required documents to OSAS.\n3. Receive examination permit and admission exam schedule.\n4. Take the admission exam.\n5. For BS Nursing, BS Med Tech, Midwifery, BSHM, BSTM, BSA, BS International Studies — interview at the College is required.\n\nSource: CvSU Citizen's Charter 2026 — OSAS, p.532.",
            "Foreign student admission sa CvSU: magbayad ng PHP 500 testing fee sa Cashier, isumite ang requirements sa OSAS (application form, TOR, visa, police clearance, affidavit of financial support, 2 pcs 1x1, atbp.). Kunin ang exam permit, kumuha ng exam, at kapag BS Nursing / Med Tech / Midwifery / BSHM / BSTM / BSA / BS Intl Studies, may interview. (Citizen's Charter 2026, p.532)",
        ],
    },
    {
        "tag": "counseling_procedure",
        "patterns": [
            "How do I book a counseling session?",
            "where to ask for counseling at CvSU",
            "I need to talk to a guidance counselor",
            "kailangan ko ng kausap, may counseling ba",
            "paano humingi ng counseling sa OSAS?",
            "is counseling free at CvSU",
            "online counseling CvSU",
            "appointment with guidance counselor",
            "i'm stressed can i see a counselor",
            "anonymous counseling?",
            "Counseling Form how to fill out",
            "walk-in counseling possible?",
            "follow-up counseling procedure",
            "do I need a referral for counseling",
            "OSAS guidance counseling steps",
        ],
        "responses": [
            "OSAS COUNSELING PROCEDURE:\n\n1. Fill out the Counseling Form (online or on-site at OSAS).\n2. Undergo initial interview with the Guidance Counselor.\n3. Fill out Appointment/Commitment Form.\n4. Attend counseling session (face-to-face or online) — 45 min to 1 hour 30 min per session.\n5. Fill out Counseling Completion Form. The counselor may follow up later.\n\nWHO MAY AVAIL: All enrolled students.\nFEES: None.\nTOTAL PROCESSING TIME: ~1 hour 10 minutes.\nSource: CvSU Citizen's Charter 2026 — OSAS, p.554.",
            "Para mag-pa-counseling sa OSAS: punan ang Counseling Form (online o on-site), mag-initial interview kay Guidance Counselor, mag-set ng appointment, dumalo sa session (45 min – 1.5 hours), at i-fill up ang completion form. Libre at para sa lahat ng enrolled students. (Citizen's Charter 2026, p.554)",
        ],
    },
    {
        "tag": "off_campus_activities",
        "patterns": [
            "How do I get approval for off-campus activity?",
            "off-campus activity procedure for student orgs",
            "field trip approval process",
            "out-of-town activity for student organization",
            "paano mag-pa-approve ng off-campus activity?",
            "may CHED memo ba para sa field trip",
            "requirements for off-campus org activity",
            "parent's permit for off-campus",
            "OSAS off-campus approval",
            "letter to OSAS for off-campus event",
            "medical clearance for off-campus activity",
            "what to do after off-campus event",
            "off-campus learning journal requirement",
            "expenditure report after off-campus activity",
            "SDS Personnel off-campus",
        ],
        "responses": [
            "OFF-CAMPUS ACTIVITIES — Student Organizations (OSAS):\n\nWHO MAY AVAIL: Recognized student organizations.\n\nREQUIREMENTS (before activity):\n- Request letter from the org president\n- Activity proposal\n- Invitation letter from the organizer\n- CHED Memorandum + list of CHED requirements (from SDS Personnel)\n- Curriculum, destination, handbook/manual\n- Notarized parent's permit\n- Medical clearance (Health Services)\n- Personnel-in-charge IDs\n- First aid kit, fees, mobility plan, insurance\n- Certificate of compliance (from SDS)\n\nREQUIREMENTS (after activity):\n- Learning journals\n- Assessment / evaluation report\n- Expenditure report\n\nPROCESS:\n1. Submit request letter to SDS for initial evaluation (or via email osasmain.studentdevelopment@cvsu.edu.ph).\n2. Receive Notice of Completion of Requirements.\n3. SDS signs and endorses to OSAS Dean → Vice President for Academic Affairs for approval.\n4. Approved letter is released to the organization.\n\nFEES: None.\nSource: CvSU Citizen's Charter 2026 — OSAS, p.540.",
            "Off-campus activity approval (student orgs): isumite ang request letter, activity proposal, invitation, CHED memo, parent's permit, medical clearance, atbp. sa SDS sa OSAS. Pagkatapos ng activity, magsumite ng learning journal, assessment report, at expenditure report. Libre. (Citizen's Charter 2026, p.540)",
        ],
    },
    {
        "tag": "library_card_replacement",
        "patterns": [
            "I lost my library card",
            "how to replace lost library card",
            "lost library account sticker",
            "library ID replacement",
            "may fees ba sa pag-replace ng library card",
            "nawala library sticker ko",
            "where to renew library card",
            "library account sticker replacement procedure",
            "I forgot my library card at home",
            "Latest Registration Form for library replacement",
            "how to validate library account",
            "library card for new student",
            "replace lost CvSU library card",
            "library re-validation each semester",
            "issuance of library account sticker",
        ],
        "responses": [
            "LIBRARY ACCOUNT STICKER REPLACEMENT:\n\nFOR STUDENTS:\n- Latest Registration Form\n- Valid CvSU ID\n(Both from the University Registrar)\n\nFOR FACULTY / EMPLOYEES:\n- CvSU identification card (from HRDO)\n\nPROCESS:\n1. Present the documents at the Library.\n2. Library staff checks/updates the database.\n3. Log the reason for the lost sticker in the logbook.\n4. Receive a new library account sticker.\n\nFEES: None.\nPROCESSING TIME: ~5 minutes.\nSource: CvSU Citizen's Charter 2026 — Library Services, p.573.",
            "Nawala ang library card / sticker? Dalhin sa Library ang latest registration form at valid CvSU ID. Mag-fill up ng logbook tungkol sa nawala, at bibigyan ka ng bagong sticker. Libre at 5 minutes lang. (Citizen's Charter 2026, p.573)",
        ],
    },
    {
        "tag": "tcp_admission",
        "patterns": [
            "how to apply for Teacher Certificate Program",
            "TCP admission CvSU",
            "I'm a non-education graduate can I teach",
            "earn education units CvSU",
            "Teacher Certificate Program requirements",
            "TCP application procedure",
            "do I need an evaluation sheet for TCP",
            "I want to become a teacher with my BS degree",
            "Notice of Admission for TCP",
            "where to apply TCP",
            "TCP application form",
            "TCP for bachelor's graduates",
            "earn teaching units to take LET",
            "apply para sa TCP",
            "Pano mag-apply ng Teacher Certificate Program?",
        ],
        "responses": [
            "TEACHER CERTIFICATE PROGRAM (TCP) ADMISSION:\n\nWHO MAY AVAIL: Bachelor's degree graduates who want to earn units in Education (e.g. to qualify for the LET).\n\nREQUIREMENTS:\n- Accomplished Application Form for Admission (download at www.cvsu.edu.ph)\n- Evaluation sheet signed by the Dean, College of Education\n- 1 pc 1x1 picture (white background)\n- 1 short brown envelope\n\nPROCESS:\n1. Submit documents to OSAS (online option may be announced).\n2. OSAS forwards to College of Education for evaluation.\n3. Receive Notice of Admission (NOA).\n4. Present NOA to University Health Services Unit for medical examination.\n\nFEES: None for application itself.\nPROCESSING TIME: ~12 minutes (multi-stage).\nSource: CvSU Citizen's Charter 2026 — OSAS, p.538.",
            "TCP (Teacher Certificate Program) — para sa mga may bachelor's degree na gustong kumuha ng education units. Magsumite sa OSAS ng application form, evaluation sheet mula sa Dean ng College of Education, 1x1 picture, at short brown envelope. Aabangan ang Notice of Admission, tapos mag-medical exam. (Citizen's Charter 2026, p.538)",
        ],
    },
    {
        "tag": "visitor_accommodation",
        "patterns": [
            "How do I visit CvSU as an outside agency?",
            "we want to tour the CvSU campus",
            "request a campus visit",
            "school visit to CvSU",
            "agency visit to CvSU",
            "benchmark visit to CvSU",
            "Pre-Visit Form CvSU",
            "PACO visitor accommodation",
            "letter of intent to visit CvSU",
            "school field trip to Cavite State University",
            "may we tour the main campus",
            "process for institutional visit",
            "Public Affairs Office CvSU visit",
            "visiting agency CvSU",
            "request letter to visit university",
        ],
        "responses": [
            "VISITOR ACCOMMODATIONS (Public Affairs and Communications Office / PACO):\n\nWHO MAY AVAIL: Any external agency or group (G2B, G2C, G2G).\n\nREQUIREMENTS:\n- Request letter addressed to the University President\n- Accomplished Pre-visit Form (PACO-QF-05)\n\nPROCESS:\n1. Submit the letter of request to the Office of the University President (OUP).\n2. PACO sends an acknowledgment receipt and provides the Pre-Visit Form.\n3. Complete the Pre-Visit Form and submit it to PACO.\n4. PACO coordinates with relevant offices (~4 days).\n5. PACO confirms the final schedule.\n6. Visit the university on the scheduled date — PACO and other offices accommodate the guests.\n\nFEES: None.\nPROCESSING TIME: ~5 days, 8 minutes (depends on length of visit).\nSource: CvSU Citizen's Charter 2026 — PACO, p.51.",
            "Para makapunta sa CvSU bilang visiting agency: magpadala ng request letter sa Office of the University President at sagutan ang Pre-Visit Form ng PACO. Mag-coordinate ang PACO sa mga office (around 4 days), kumpirmahin ang schedule, at puntahan sa nakatakdang araw. Libre. (Citizen's Charter 2026, p.51)",
        ],
    },
]


def backup(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bk = path.with_suffix(path.suffix + f".bak_{stamp}")
    shutil.copy2(path, bk)
    return bk


def main() -> int:
    if not INTENTS_PATH.exists():
        print(f"missing: {INTENTS_PATH}")
        return 1
    if not RESPONSES_PATH.exists():
        print(f"missing: {RESPONSES_PATH}")
        return 1

    with INTENTS_PATH.open(encoding="utf-8") as f:
        intents_doc = json.load(f)
    with RESPONSES_PATH.open(encoding="utf-8") as f:
        responses = json.load(f)

    existing_tags = {it["tag"] for it in intents_doc["intents"]}
    added, skipped = [], []
    for ni in NEW_INTENTS:
        if ni["tag"] in existing_tags:
            skipped.append(ni["tag"])
            continue
        intents_doc["intents"].append({
            "tag": ni["tag"],
            "patterns": ni["patterns"],
            "responses": ni["responses"],
        })
        responses[ni["tag"]] = ni["responses"]
        added.append(ni["tag"])

    if not added:
        print("No new intents to add (all tags already present).")
        return 0

    print(f"Backing up: {backup(INTENTS_PATH).name}")
    print(f"Backing up: {backup(RESPONSES_PATH).name}")

    with INTENTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(intents_doc, f, ensure_ascii=False, indent=2)
    with RESPONSES_PATH.open("w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)

    print(f"\nAdded {len(added)} intents:")
    for t in added:
        print(f"  + {t}")
    if skipped:
        print(f"\nSkipped {len(skipped)} (already existed):")
        for t in skipped:
            print(f"  - {t}")
    print("\nNext: python training/train_hybrid.py  (from repo root)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
