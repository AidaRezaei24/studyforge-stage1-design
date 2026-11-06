"""Rebuild the report from reviewed Markdown, diagrams, and real Git history.

Install the optional report dependency with: python -m pip install -e '.[report]'
The checked-in diagram PNGs have editable Graphviz .dot sources beside them.
"""
from html import escape
from pathlib import Path
import re
import subprocess
import unittest

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Flowable, KeepTogether
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
ACCENT = colors.HexColor('#355342')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('Body', fontName='Helvetica', fontSize=10, leading=15,
                          textColor=colors.HexColor('#26342b'), spaceAfter=9))
styles.add(ParagraphStyle('SmallBody', parent=styles['Body'], fontSize=9, leading=13))
styles['Heading1'].fontSize = 22
styles['Heading1'].leading = 27
styles['Heading1'].textColor = ACCENT
styles['Heading1'].spaceAfter = 16
styles['Heading2'].fontSize = 15
styles['Heading2'].leading = 20
styles['Heading2'].textColor = ACCENT
styles['Heading2'].spaceBefore = 15
styles['Heading2'].spaceAfter = 10
styles['Heading3'].fontSize = 12
styles['Heading3'].fontName = 'Helvetica-Bold'
styles['Heading3'].leading = 16
styles['Heading3'].textColor = ACCENT
styles['Heading3'].spaceBefore = 12
styles['Heading3'].spaceAfter = 8


def rich(text):
    text = escape(text).replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', ' - ')
    text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#355342">\1</link>', text)
    return text


def section(text, name):
    start = text.index('## ' + name)
    end = text.find('\n## ', start + 3)
    return text[start:end if end != -1 else None]


class Sequence(Flowable):
    """Vector UML sequence with explicit calls, returns and persisted checkpoints."""
    def __init__(self, title, lanes, messages):
        super().__init__()
        self.title, self.lanes, self.messages = title, lanes, messages
        self.width, self.height = 483, 72 + len(messages) * 35

    def draw(self):
        c = self.canv
        c.setFillColor(ACCENT)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(0, self.height - 12, self.title)
        count = len(self.lanes)
        xs = [35 + i * 412 / (count - 1) for i in range(count)]
        top = self.height - 45
        for x, label in zip(xs, self.lanes):
            c.setFillColor(colors.HexColor('#eef3ec'))
            c.setStrokeColor(ACCENT)
            c.rect(x - 35, top - 10, 70, 23, fill=1)
            c.setFillColor(ACCENT)
            c.setFont('Helvetica-Bold', 7)
            c.drawCentredString(x, top - 1, label)
            c.setDash(2, 3)
            c.line(x, top - 10, x, 10)
            c.setDash()
        for i, (a, b, label, returned) in enumerate(self.messages):
            y = top - 35 - i * 35
            x1, x2 = xs[a], xs[b]
            c.setStrokeColor(ACCENT)
            c.setFillColor(ACCENT)
            c.setLineWidth(.7)
            c.setDash(3, 2) if returned else c.setDash()
            c.line(x1, y, x2, y)
            c.setDash()
            direction = 1 if x2 > x1 else -1
            c.line(x2, y, x2 - direction * 5, y + 3)
            c.line(x2, y, x2 - direction * 5, y - 3)
            c.setFont('Helvetica', 7.2)
            c.drawString(min(x1, x2) + 3, y + 5, f'{i + 1}. {label}')


def markdown(text, story):
    lines = text.splitlines()
    paragraph, table, fenced = [], [], False

    def flush():
        if paragraph:
            story.append(Paragraph(rich(' '.join(paragraph)), styles['Body']))
            paragraph.clear()

    def flush_table():
        if not table:
            return
        headers = table[0]
        for row in table[1:]:
            if all(re.fullmatch(r':?-+:?', item.replace(' ', '')) for item in row):
                continue
            items = [Paragraph(f'<b>{rich(heading)}:</b> {rich(cell)}', styles['SmallBody'])
                     for heading, cell in zip(headers, row)]
            items.append(Spacer(1, 6))
            story.append(KeepTogether(items))
        table.clear()

    for line in lines:
        if line.startswith('```'):
            flush(); flush_table(); fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith('|'):
            flush()
            table.append([s.strip() for s in line.strip().strip('|').split('|')])
            continue
        flush_table()
        if line.startswith('#'):
            flush()
            n = len(line) - len(line.lstrip('#'))
            story.append(Paragraph(rich(line[n:].strip()), styles[f'Heading{min(n, 3)}']))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
    flush(); flush_table()


def footer(c, doc):
    w, h = A4
    c.setStrokeColor(colors.HexColor('#ccd6c9'))
    c.line(55, h - 40, w - 55, h - 40)
    c.setFont('Helvetica', 8)
    c.setFillColor(ACCENT)
    c.drawString(55, h - 31, 'STUDYFORGE  /  STAGE 2 IMPLEMENTATION')
    c.drawString(55, 31, 'EECS3311  |  November 12, 2026  |  Live validation and videos pending')
    c.drawRightString(w - 55, 31, str(doc.page))


def build():
    architecture = (ROOT / 'docs/architecture.md').read_text()
    development = (ROOT / 'docs/development-log.md').read_text()
    feature_map = (ROOT / 'docs/feature-map.md').read_text()
    test_count = unittest.defaultTestLoader.discover(str(ROOT / 'tests')).countTestCases()
    log = subprocess.run(['git', 'log', 'ee6d35a..HEAD', '--format=%H%x09%aI%x09%s'], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    commit_paragraphs = []
    for row in log.splitlines():
        sha, timestamp, subject = row.split('\t', 2)
        commit_paragraphs.append(f'[{sha[:7]}](https://github.com/AidaRezaei24/studyforge-stage1-design/commit/{sha}) / {timestamp} / {subject}')
    overview = '''# StudyForge
## Stage 2 Implementation Report

EECS3311 Software Design / Fall 2026 / Prepared November 12, 2026, Toronto local time.

### 1 Project overview and implementation status

StudyForge helps a university student turn course materials into evidence-linked
explanations, practice and scheduled study actions. A local browser GUI and CLI
share the same controller, commands, SQLite records and feature services. Source
code now implements a path for each of the twelve original Stage 1 features and
seven distinct design patterns. The original main branch contained only the Stage
1 report and submission link; there was no earlier runnable application.

The production adapter calls OpenAI Responses with the configured Stage 1 model,
gpt-4.1-mini-2025-04-14. Retrieval and recent conversation memory bound the context;
strategies validate output schemas and citation identities before saving artifacts.
The focused-session orchestrator selects registered explanation and practice tools,
reads current progress to choose practice, and checkpoints results and legal state
transitions. This is a multi-step agent workflow rather than a raw prompt-forwarding
interface. Deterministic policies control grading, dates, workload, approvals,
calendar conflicts, review intervals and learning metrics.

Verification status: TEST_COUNT automated tests passed, including complete CLI and local
HTTP API journeys through all twelve features with real SQLite persistence and
reopening. Only the remote model is replaced by a test double in those journeys.
The GUI was manually inspected for course creation, real material import and safe
missing-key errors. A stale-output defect discovered in that check was corrected.
Local API configuration is now in place. Initial provider requests exposed a
JSON-mode input requirement, which was corrected and regression-tested. No live
generated output has yet been accepted; full live feature validation is pending.

Submission is not complete. The owner will complete API access, validate actual
generated output, record and upload all feature demonstrations, add accessible
timestamped links, supply measured AI usage/cost accounting and submit the course
repository URL. Historical weekly activity is absent in the original repository;
current commits do not establish development or pushes in the required past periods.
The original November 10 deadline has passed. No grade or on-time status is claimed.

Scope changes are explicit: lexical retrieval replaces embeddings; browser GUI
replaces a native window; local ICS export replaces remote calendar writes; basic
descriptive analytics and bounded sessions replace broader planned behavior.
Sections 2-4 account for every original feature and affected class/pattern.
'''
    story = []
    markdown(overview.replace('TEST_COUNT', str(test_count)), story)
    story.append(PageBreak())
    parts = re.split(r'(?=^## F\d{2} )', feature_map, flags=re.M)
    markdown('# 2 Feature to implementation mapping\n' + '\n'.join(parts[0].splitlines()[1:]), story)
    for index, part in enumerate(parts[1:]):
        if index and index % 2 == 0:
            story.append(PageBreak())
        items = []
        markdown(part, items)
        story.append(KeepTogether(items))
    story.append(PageBreak())
    markdown('# 3 Implemented design patterns\n' + '\n'.join(section(architecture, 'Seven implemented patterns').splitlines()[1:]), story)
    markdown('## Updated UML class diagrams\nFigures split the same implementation into four readable views. Solid arrows show dependencies; open triangle arrowheads show inheritance; dashed open triangles show protocol implementation. Repeated classes are references to the same class. CLI/HTTP are module boundaries, not invented Python classes. The complete editable relationship model and updated use-case diagram are in docs/architecture.md.', story)
    for name, caption in [('application', 'Application boundary, commands, facade and persistence'),
                          ('runtime', 'Session State participants, tools and Observer participants'),
                          ('learning', 'Learning services, source ingestion and scoped retrieval'),
                          ('strategies', 'Generation Strategy participants and model Adapter')]:
        story.append(PageBreak())
        story.append(Paragraph(caption, styles['Heading2']))
        path = ROOT / f'docs/diagrams/{name}.png'
        width, height = PILImage.open(path).size
        scale = min(483 / width, 630 / height)
        story.append(Image(str(path), width=width * scale, height=height * scale))
        story.append(Spacer(1, 12))
        story.append(Paragraph('Editable source: docs/diagrams/' + name + '.dot. The full source-level relationship diagram is also available in docs/architecture.md.', styles['SmallBody']))
    story.append(PageBreak())
    markdown('## Updated use-case diagram\nThe same student can invoke UC01-UC12 through either local interface. Source ingestion uses local files; generated learning activities use the OpenAI adapter; reminders are local ICS exports for manual import, replacing the remote-calendar actor from Stage 1.', story)
    path = ROOT / 'docs/diagrams/usecases.png'
    width, height = PILImage.open(path).size
    scale = min(483 / width, 590 / height)
    story.append(Image(str(path), width=width * scale, height=height * scale))
    story.append(PageBreak())
    markdown('## Updated grounded-generation sequence\nApplies to F02/F03/F04/F06/F07. A retrieval gap stops before the model call; invalid output is retried once and never persisted if still invalid.', story)
    story.append(Sequence('Grounded generation / principal success path', ['GUI / CLI', 'Controller', 'Learning', 'Strategy', 'Model', 'SQLite'], [
        (0, 1, 'handle(feature, course, input)', False),
        (1, 5, 'validate course exists', False),
        (1, 2, 'command.execute()', False),
        (2, 5, 'retrieve course-scoped chunks', False),
        (5, 2, 'evidence + stable locations', True),
        (2, 3, 'generate(evidence, contract)', False),
        (3, 4, 'Responses API request', False),
        (4, 3, 'JSON; verify schema/citations', True),
        (3, 4, 'once only if invalid: retry', False),
        (3, 2, 'validated artifact', True),
        (2, 5, 'save artifact + evidence', False),
        (2, 0, 'result, sources, coverage', True)]))
    story.append(PageBreak())
    markdown('## Updated focused-session sequence\nF12 now runs three bounded stages. Pause/resume/skip/stop are legal at checkpoints. Tool failures persist a paused state; expiry ends work before another tool is called. The student submits generated quiz answers through ordinary grading before review when desired.', story)
    story.append(Sequence('Focused session / checkpointed activity path', ['Student/UI', 'Controller', 'Orchestrator', 'State', 'Tools', 'SQLite'], [
        (0, 1, 'session_start(course, goal, minutes)', False),
        (1, 2, 'start()', False),
        (2, 5, 'save learn checkpoint + budget', False),
        (0, 2, 'advance', False),
        (2, 3, 'validate legal action and budget', False),
        (2, 4, 'grounded ask(goal)', False),
        (2, 5, 'save explanation; state=practice', False),
        (0, 2, 'pause/resume or advance', False),
        (2, 4, 'quiz(weak topic, difficulty)', False),
        (2, 5, 'save quiz; state=review', False),
        (0, 1, 'grade quiz answers (optional)', False),
        (0, 2, 'advance; read current progress', False),
        (2, 5, 'save review; state=completed', False)]))
    additional = [
        ('F01 / SD01 Ingest and index',
         'Each file has its own transaction. Duplicate hashes are reported without new records. Unsupported, encrypted, empty or oversized files produce per-file errors; a parser/event failure rolls back that file. No embeddings or model-generated metadata are claimed.',
         ['GUI / CLI', 'Controller', 'Learning', 'IngestTool', 'SQLite', 'EventBus'], [
             (0, 1, 'import_materials(course, paths)', False), (1, 2, 'execute import command', False),
             (2, 3, 'execute(course, paths)', False), (3, 4, 'read known hashes for course', False),
             (3, 4, 'begin per-file transaction', False), (3, 4, 'save extracted lexical chunks', False),
             (3, 5, 'publish MaterialIndexed', False), (5, 4, 'observer saves activity event', False),
             (3, 4, 'commit file or rollback failure', False), (3, 0, 'imported / duplicates / errors', True)]),
        ('F05 / SD03 Plan, validate and approve',
         'The model orders evidence-linked topics using goal and mastery. Deadline, daily capacity and known graph prerequisites are enforced locally. Infeasible plans fail before saving; replacing an approved plan requires explicit replacement confirmation.',
         ['GUI / CLI', 'Controller', 'Facade', 'Model', 'SQLite', 'Progress'], [
             (0, 1, 'plan_create(goal, deadline, capacity)', False), (1, 2, 'execute plan command', False),
             (2, 5, 'get_snapshot(course)', False), (2, 4, 'retrieve evidence and known graph', False),
             (2, 3, 'generate ordered topics', False), (3, 2, 'topics; locally validate constraints', True),
             (2, 4, 'save feasible draft plan', False), (2, 0, 'preview dated sessions', True),
             (0, 2, 'plan_approve(id, replace)', False), (2, 4, 'transaction: replace old, approve new', False),
             (2, 0, 'approved plan', True)]),
        ('F06 / SD11 Review and next due date',
         'Only ratings 0-3 are accepted. Rejected cards cannot be reviewed. The updated card and CardReviewed event are saved atomically. Due queues exclude rejected cards and cards scheduled after the requested date.',
         ['GUI / CLI', 'Controller', 'Facade', 'Scheduler', 'SQLite', 'EventBus'], [
             (0, 1, 'review(card_id, rating)', False), (1, 2, 'execute review command', False),
             (2, 4, 'locate saved, non-rejected card', False), (2, 3, 'schedule_next(card, rating)', False),
             (3, 2, 'interval, due date, review count', True), (2, 4, 'save updated deck in transaction', False),
             (2, 5, 'publish CardReviewed', False), (5, 4, 'observer saves review event', False),
             (2, 0, 'updated interval and due date', True), (0, 1, 'due_queue(course)', False),
             (1, 0, 'eligible cards from saved decks', True)]),
        ('F08 / SD05 Grade and retain rubric',
         'Completeness and attempt-ID duplicate checks happen before scoring. Choice grading is deterministic. Free-text grades must have bounded score/confidence and nonempty feedback. Low-confidence items are flagged and excluded from mastery; invalid results roll back the attempt.',
         ['GUI / CLI', 'Controller', 'Assessment', 'Model', 'SQLite', 'EventBus'], [
             (0, 1, 'grade(quiz, all answers, attempt ID)', False), (1, 2, 'execute grade command', False),
             (2, 4, 'load quiz and check attempt ID', False), (2, 3, 'free answers: rubric + evidence', False),
             (3, 2, 'score, feedback, confidence', True), (2, 4, 'save result, evidence, rubric snapshot', False),
             (2, 5, 'publish AttemptRecorded', False), (5, 4, 'observer saves activity event', False),
             (2, 0, 'total, item feedback and flags', True)]),
        ('F09 / SD09 Diagnose and confirm practice',
         'At least two observations on a topic and mastery below 0.7 are needed. Otherwise no diagnosis or generation is claimed. Confirmation generates a quiz using the chosen difficulty; adaptation does not silently replace an active plan.',
         ['GUI / CLI', 'Controller', 'Facade', 'Progress', 'Learning', 'SQLite'], [
             (0, 1, 'adapt(course, minutes)', False), (1, 2, 'execute adaptation command', False),
             (2, 3, 'get_snapshot(course)', False), (3, 5, 'read accepted attempts/reviews', False),
             (3, 2, 'topic means and sample counts', True), (2, 0, 'proposal or insufficient evidence', True),
             (0, 2, 'adapt(confirm=true)', False), (2, 4, 'quiz(topic, count, difficulty)', False),
             (4, 5, 'save validated quiz', False), (2, 5, 'save adaptation record', False),
             (2, 0, 'generated practice and reason', True)]),
        ('F10 / SD10 Compute progress snapshot',
         'The snapshot derives deterministic means and counts from saved attempts and events. Low-confidence grade items are excluded. Empty data returns empty topics and zero counts; no trend or calibrated mastery claim is invented.',
         ['GUI / CLI', 'Controller', 'Facade', 'Progress', 'SQLite', 'View'], [
             (0, 1, 'progress(course)', False), (1, 2, 'execute progress command', False),
             (2, 3, 'get_snapshot(course)', False), (3, 4, 'read attempts and events', False),
             (3, 4, 'read plans and session states', False), (4, 3, 'stored observations', True),
             (3, 2, 'means, samples, counts, as_of', True), (2, 5, 'render measured snapshot', True)]),
        ('F11 / SD08 Confirm local reminders and export',
         'This replaces the original remote-calendar sequence. Only approved plans are scheduled. Candidate dates are checked for timezone/DST, midnight and conflicts across all local courses. Preview does not write; confirmation uses stable reminder IDs. An export failure leaves confirmed local reminders available for retry. Manual calendar import is a user step.',
         ['GUI / CLI', 'Controller', 'Facade', 'SQLite', 'ICS Adapter', 'Calendar app'], [
             (0, 1, 'schedule(plan, time, timezone)', False), (1, 2, 'execute scheduling command', False),
             (2, 3, 'load approved plan + all reminders', False), (2, 0, 'validated preview; no writes', True),
             (0, 2, 'schedule(confirm=true, path)', False), (2, 3, 'upsert stable session reminder IDs', False),
             (2, 4, 'export confirmed reminders to ICS', False), (4, 0, 'file path or retryable file error', True),
             (0, 5, 'manually import ICS file', False)])]
    for title, explanation, lanes, messages in additional:
        story.append(PageBreak())
        markdown('## Updated sequence: ' + title + '\n' + explanation, story)
        story.append(Sequence(title, lanes, messages))
    story.append(PageBreak())
    changes = section(architecture, 'Consolidated feature and class change record').split('\nCourse creation,')[0]
    markdown('# 4 Changes and rationale\n' + '\n'.join(changes.splitlines()[1:]), story)
    story.append(PageBreak())
    markdown('# 5 AI tools and collaboration log\n' + development.split('## Weekly code activity')[0], story)
    story.append(PageBreak())
    markdown('# 6 Development and verification summary\n' + section(development, 'Weekly code activity, Toronto local dates'), story)
    markdown('## Current implementation commits\nThese are actual implementation commits available when this report was generated, not substitutes for missing historical activity. The report-packaging commit itself is not listed.\n' + '\n\n'.join(commit_paragraphs), story)
    markdown('## Reproduction and remaining gates\nRun python -m unittest discover -s tests -v and make check after installing with python -m pip install -e . . The suite passed ' + str(test_count) + ' tests at the final verification recorded for this report. Python compilation, JavaScript syntax, credential scanning, package installation and PDF visual checks are separate release checks. No Stage 3 KUMA validation is claimed.\n\nA production launch without credentials must show a configuration error; test fixtures are never accepted as live LLM evidence. Record actual live results before claiming final feature acceptance. Confirm all source/report files are pushed to the public repository and verify video access signed out before course submission.', story)
    story.append(PageBreak())
    markdown('# 7 Demonstration index\nThe owner selected the recording-guide workflow. No videos have yet been recorded or supplied in this session. All twelve rows remain pending; no accessible link or real timestamp is invented. docs/demonstrations.md contains exact GUI/CLI invocation, input, expected result, alternative/error and AI explanation for each segment. docs/demo-index.json is the machine-readable index to update after uploading.\n\nA combined recording is acceptable only when each feature has a direct timestamped link. Record the running application with the real provider and show both GUI and CLI collectively; screenshots, this report and test fixtures are not video demonstrations. Avoid recording .env or account credentials.', story)
    for i in range(1, 13):
        feature = re.search(r'^## (F%02d .+)$' % i, feature_map, re.M).group(1)
        markdown('### ' + feature + '\nStatus: awaiting owner recording and upload. Video link: not supplied. Actual timestamp: not supplied. Planned segment: F%02d. See the same feature heading in docs/demonstrations.md.' % i, story)
    markdown('## References and final ownership\nStage 1 source: StudyForge_Stage1_Project_Design_Report.pdf (40 pages, unchanged). Stage 2 requirements: Project-Stage2-Instruction.pdf (5 pages, supplied locally; not republished without need).\n\nOfficial API contract: [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs). JSON mode guarantees JSON shape only; application validators provide feature-level checks.\n\nThe student must review and understand the code, verify model output and billing, complete recordings and submit the repository through the course system. This report describes verified source and explicit limitations rather than claiming every submission gate has passed.', story)
    doc = SimpleDocTemplate(str(ROOT / 'stage2-report.pdf'), pagesize=A4, leftMargin=55, rightMargin=55,
                            topMargin=60, bottomMargin=55, title='StudyForge Stage 2 Implementation Report',
                            author='StudyForge project / AidaRezaei24')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print('Generated stage2-report.pdf from reviewed project sources.')


if __name__ == '__main__':
    build()
