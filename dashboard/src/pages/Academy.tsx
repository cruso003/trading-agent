import { useNavigate } from 'react-router-dom';
import { Lock, BookOpen, CheckCircle } from 'lucide-react';
import { useAllProgress } from '../hooks/useProgress';
import './Academy.css';

interface Module {
  num: string;
  title: string;
  description: string;
  lessons: Lesson[];
  available: boolean;
}

interface Lesson {
  title: string;
  done: boolean;
}

const MODULES: Module[] = [
  {
    num: '01',
    title: 'Understanding the Gold Market',
    description:
      'What moves gold, why it behaves differently from forex pairs, and why XAUUSD is the primary focus of this system.',
    available: true,
    lessons: [
      { title: 'Why gold? The case for XAUUSD', done: false },
      { title: 'What drives gold price — macro fundamentals', done: false },
      { title: 'Session structure and the London-NY overlap', done: false },
      { title: 'Reading market structure on gold charts', done: false },
    ],
  },
  {
    num: '02',
    title: 'How the AI Reads Setups',
    description:
      'A breakdown of the three-pillar analysis framework the AI uses, the prefilter logic, and how decisions are graded.',
    available: false,
    lessons: [
      { title: 'The three pillars: Trend, Momentum, Location', done: false },
      { title: 'The prefilter — what gets blocked and why', done: false },
      { title: 'A+ vs B grade setups', done: false },
      { title: 'Reading the decision log', done: false },
    ],
  },
  {
    num: '03',
    title: 'Risk Management',
    description:
      'Position sizing, stop loss logic, the 2% rule, and how to protect your account when setups fail.',
    available: false,
    lessons: [
      { title: 'The 2% rule — position sizing by account size', done: false },
      { title: 'Stop loss placement — structure vs fixed', done: false },
      { title: 'Managing the trade after entry', done: false },
      { title: 'The daily drawdown limit and when to stop', done: false },
    ],
  },
  {
    num: '04',
    title: 'Trading Psychology',
    description:
      'Why discipline is the hardest part, how to handle consecutive losses, and building habits that last.',
    available: false,
    lessons: [
      { title: 'Detaching from outcomes', done: false },
      { title: 'Journaling and reviewing your own trades', done: false },
      { title: 'Handling drawdown without breaking rules', done: false },
      { title: 'Building the right routine', done: false },
    ],
  },
];

export default function Academy() {
  const navigate = useNavigate();
  const progress = useAllProgress();

  function lessonDone(moduleNum: number, lessonNum: number): boolean {
    return progress[`${moduleNum}-${lessonNum}`] === true;
  }

  return (
    <div className="academy-page">
      <div className="academy-inner">

        <div className="academy-header">
          <h1 className="academy-title">Academy</h1>
          <p className="academy-subtitle">
            Four modules. Built on the same framework the AI runs on.
          </p>
        </div>

        <div className="academy-modules">
          {MODULES.map((mod, modIdx) => (
            <div
              className={`academy-module ${mod.available ? 'module-available' : 'module-locked'}`}
              key={mod.num}
            >
              <div className="academy-module-header">
                <div className="academy-module-num mono">{mod.num}</div>
                <div className="academy-module-meta">
                  <h2 className="academy-module-title">{mod.title}</h2>
                  <p className="academy-module-desc">{mod.description}</p>
                </div>
                <div className="academy-module-status">
                  {mod.available ? (
                    <span className="academy-badge badge-available">
                      <BookOpen size={11} />
                      Available
                    </span>
                  ) : (
                    <span className="academy-badge badge-soon">
                      <Lock size={11} />
                      Coming Soon
                    </span>
                  )}
                </div>
              </div>

              <div className="academy-lessons">
                {mod.lessons.map((lesson, i) => {
                  const done = lessonDone(modIdx + 1, i + 1);
                  return (
                    <div
                      className={`academy-lesson ${!mod.available ? 'lesson-locked' : ''}`}
                      key={i}
                      onClick={() => mod.available && navigate(`/academy/lesson/${modIdx + 1}/${i + 1}`)}
                    >
                      <span className="academy-lesson-icon">
                        {done ? (
                          <CheckCircle size={13} className="icon-done" />
                        ) : mod.available ? (
                          <span className="lesson-dot" />
                        ) : (
                          <Lock size={11} className="icon-lock" />
                        )}
                      </span>
                      <span className="academy-lesson-title">{lesson.title}</span>
                      {mod.available && (
                        <span className="academy-lesson-action">
                          {done ? 'Review' : 'Start'}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="academy-footer-note">
          Content is added module by module. You'll be notified when new lessons go live.
        </div>
      </div>
    </div>
  );
}
