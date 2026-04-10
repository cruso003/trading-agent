import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight, CheckCircle, ChevronLeft } from 'lucide-react';
import { getLesson, getNextLesson, getPrevLesson } from '../data/lessonData';
import { useProgress } from '../hooks/useProgress';
import './LessonPage.css';

export default function LessonPage() {
  const { module, lesson } = useParams<{ module: string; lesson: string }>();
  const navigate = useNavigate();

  const moduleNum = parseInt(module ?? '1', 10);
  const lessonNum = parseInt(lesson ?? '1', 10);

  const data = getLesson(moduleNum, lessonNum);
  const next = getNextLesson(moduleNum, lessonNum);
  const prev = getPrevLesson(moduleNum, lessonNum);

  const { isComplete, markComplete } = useProgress(moduleNum, lessonNum);

  if (!data) {
    return (
      <div className="lesson-notfound">
        <p>Lesson not found.</p>
        <Link to="/academy">← Back to Academy</Link>
      </div>
    );
  }

  return (
    <div className="lesson-page">
      <div className="lesson-inner">

        {/* Breadcrumb */}
        <div className="lesson-breadcrumb">
          <Link to="/academy" className="lesson-back">
            <ChevronLeft size={14} />
            <span>Academy</span>
          </Link>
          <span className="lesson-breadcrumb-sep">/</span>
          <span className="lesson-breadcrumb-module">Module {String(moduleNum).padStart(2, '0')}</span>
        </div>

        {/* Header */}
        <div className="lesson-header">
          <div className="lesson-meta">
            <span className="lesson-module-label">{data.moduleTitle}</span>
            <span className="lesson-read-time">{data.readingTime}</span>
          </div>
          <h1 className="lesson-title">{data.title}</h1>
        </div>

        {/* Body */}
        <div className="lesson-body">
          {data.sections.map((section, i) => {
            if (section.type === 'subheading') {
              return (
                <h2 className="lesson-subheading" key={i}>
                  {section.content as string}
                </h2>
              );
            }

            if (section.type === 'paragraph') {
              return (
                <p className="lesson-paragraph" key={i}>
                  {section.content as string}
                </p>
              );
            }

            if (section.type === 'callout') {
              return (
                <div className="lesson-callout" key={i}>
                  <p>{section.content as string}</p>
                </div>
              );
            }

            if (section.type === 'numbered_list') {
              return (
                <ol className="lesson-list lesson-list-numbered" key={i}>
                  {(section.content as string[]).map((item, j) => (
                    <li key={j}>{item}</li>
                  ))}
                </ol>
              );
            }

            if (section.type === 'bullet_list') {
              return (
                <ul className="lesson-list lesson-list-bullet" key={i}>
                  {(section.content as string[]).map((item, j) => (
                    <li key={j}>{item}</li>
                  ))}
                </ul>
              );
            }

            return null;
          })}
        </div>

        {/* Key takeaways */}
        <div className="lesson-takeaways">
          <div className="lesson-takeaways-title">Key Takeaways</div>
          <ul className="lesson-takeaways-list">
            {data.takeaways.map((t, i) => (
              <li key={i}>
                <CheckCircle size={13} className="lesson-takeaway-icon" />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Mark complete + nav */}
        <div className="lesson-footer">
          {!isComplete ? (
            <button className="lesson-complete-btn" onClick={markComplete}>
              <CheckCircle size={14} />
              Mark as complete
            </button>
          ) : (
            <span className="lesson-completed-badge">
              <CheckCircle size={14} />
              Completed
            </span>
          )}

          <div className="lesson-nav">
            {prev ? (
              <button
                className="lesson-nav-btn"
                onClick={() => navigate(`/academy/lesson/${prev.moduleNum}/${prev.lessonNum}`)}
              >
                <ArrowLeft size={14} />
                <span>Previous</span>
              </button>
            ) : (
              <div />
            )}

            {next ? (
              <button
                className="lesson-nav-btn lesson-nav-btn-next"
                onClick={() => navigate(`/academy/lesson/${next.moduleNum}/${next.lessonNum}`)}
              >
                <span>Next lesson</span>
                <ArrowRight size={14} />
              </button>
            ) : (
              <button
                className="lesson-nav-btn lesson-nav-btn-next"
                onClick={() => navigate('/academy')}
              >
                <span>Back to Academy</span>
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
