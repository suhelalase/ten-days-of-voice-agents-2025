'use client';

import { Button } from '@/components/livekit/button';
import { motion } from 'motion/react';

// Clean wellness icon without glow effects
function WellnessIcon() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="relative mb-8"
    >
      <svg
        width="120"
        height="120"
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="mx-auto"
      >
        {/* Meditation Person */}
        <g className="animate-pulse-slow">
          {/* Head */}
          <circle cx="60" cy="30" r="12" fill="url(#gradientPrimary)" />

          {/* Body */}
          <path
            d="M60 46 
               C60 46, 45 52, 40 62
               L40 82
               C40 84.5, 42 86.5, 44.5 86.5
               L52 86.5
               L52 105
               C52 107.5, 54 109.5, 56.5 109.5
               L63.5 109.5
               C66 109.5, 68 107.5, 68 105
               L68 86.5
               L75.5 86.5
               C78 86.5, 80 84.5, 80 82
               L80 62
               C75 52, 60 46, 60 46 Z"
            fill="url(#gradientPrimary)"
          />

          {/* Lotus base */}
          <ellipse cx="60" cy="85" rx="24" ry="5" fill="url(#gradientSecondary)" opacity="0.3" />
        </g>

        {/* Gradient definitions */}
        <defs>
          <linearGradient id="gradientPrimary" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgb(119, 93, 208)" />
            <stop offset="100%" stopColor="rgb(208, 93, 176)" />
          </linearGradient>
          <linearGradient id="gradientSecondary" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgb(208, 93, 176)" />
            <stop offset="100%" stopColor="rgb(238, 147, 103)" />
          </linearGradient>
        </defs>
      </svg>
    </motion.div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="bg-background relative h-screen overflow-hidden">
      {/* Clean section without backdrop blur */}
      <section className="relative flex h-full flex-col items-center justify-center px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="max-w-3xl"
        >
          <WellnessIcon />

          {/* Main heading with gradient text */}
          <h1
            className="mb-6 text-5xl font-bold leading-tight md:text-6xl lg:text-7xl"
            style={{
              backgroundImage: 'linear-gradient(135deg, rgb(119, 93, 208) 0%, rgb(208, 93, 176) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Your Daily Wellness Companion
          </h1>

          <p className="text-muted-foreground mx-auto mb-4 max-w-xl text-lg leading-relaxed md:text-xl">
            Check in with yourself. Set daily intentions. Build healthy habits.
          </p>

          <p className="text-foreground/70 mx-auto mb-10 max-w-md leading-relaxed">
            Start a voice conversation to reflect on your mood, energy, and goals for the day.
          </p>

          {/* CTA Button with clean gradient */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            className="mb-12"
          >
            <Button
              variant="primary"
              size="lg"
              onClick={onStartCall}
              className="relative overflow-hidden px-10 py-6 text-lg font-semibold shadow-lg transition-shadow hover:shadow-xl"
              style={{
                background: 'linear-gradient(135deg, rgb(119, 93, 208) 0%, rgb(208, 93, 176) 100%)',
                border: 'none',
              }}
            >
              <span className="relative z-10">{startButtonText}</span>
            </Button>
          </motion.div>

          {/* Feature pills - refined design */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="flex flex-wrap justify-center gap-3"
          >
            {[
              { text: 'Track Mood', gradient: 'linear-gradient(135deg, rgb(119, 93, 208) 0%, rgb(208, 93, 176) 100%)' },
              { text: 'Set Goals', gradient: 'linear-gradient(135deg, rgb(232, 103, 159) 0%, rgb(238, 147, 103) 100%)' },
              { text: 'Daily Reflection', gradient: 'linear-gradient(135deg, rgb(96, 93, 208) 0%, rgb(119, 147, 208) 100%)' }
            ].map((feature, i) => (
              <motion.div
                key={feature.text}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 + i * 0.1, duration: 0.4 }}
                className="bg-card border-border flex items-center gap-2 rounded-full border px-6 py-2.5 text-sm font-medium shadow-sm transition-shadow hover:shadow-md"
              >
                <span
                  className="flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold text-white"
                  style={{ background: feature.gradient }}
                >
                  ✓
                </span>
                <span className="text-foreground">{feature.text}</span>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* Footer - clean and simple */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.5 }}
        className="fixed bottom-6 left-0 flex w-full items-center justify-center px-6"
      >
        <p className="text-muted-foreground text-center text-xs md:text-sm">
          Powered by AI voice technology •{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="text-primary hover:text-primary/80 underline underline-offset-4 transition-colors"
          >
            Learn more
          </a>
        </p>
      </motion.div>
    </div>
  );
};
