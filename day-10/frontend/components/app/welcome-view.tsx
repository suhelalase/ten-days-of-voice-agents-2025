import { Button } from '@/components/livekit/button';

function WelcomeImage() {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-fg0 mb-6 size-20 drop-shadow-[0_0_12px_rgba(58,207,255,0.8)]"
    >
      <path
        d="M15 24V40C15 40.7957 14.6839 41.5587 14.1213 42.1213C13.5587 42.6839 12.7956 43 12 43C11.2044 43 10.4413 42.6839 9.87868 42.1213C9.31607 41.5587 9 40.7957 9 40V24C9 23.2044 9.31607 22.4413 9.87868 21.8787C10.4413 21.3161 11.2044 21 12 21C12.7956 21 13.5587 21.3161 14.1213 21.8787C14.6839 22.4413 15 23.2044 15 24ZM22 5C21.2044 5 20.4413 5.31607 19.8787 5.87868C19.3161 6.44129 19 7.20435 19 8V56C19 56.7957 19.3161 57.5587 19.8787 58.1213C20.4413 58.6839 21.2044 59 22 59C22.7956 59 23.5587 58.6839 24.1213 58.1213C24.6839 57.5587 25 56.7957 25 56V8C25 7.20435 24.6839 6.44129 24.1213 5.87868C23.5587 5.31607 22.7956 5 22 5ZM32 13C31.2044 13 30.4413 13.3161 29.8787 13.8787C29.3161 14.4413 29 15.2044 29 16V48C29 48.7957 29.3161 49.5587 29.8787 50.1213C30.4413 50.6839 31.2044 51 32 51C32.7956 51 33.5587 50.6839 34.1213 50.1213C34.6839 49.5587 35 48.7957 35 48V16C35 15.2044 34.6839 14.4413 34.1213 13.8787C33.5587 13.3161 32.7956 13 32 13ZM42 21C41.2043 21 40.4413 21.3161 39.8787 21.8787C39.3161 22.4413 39 23.2044 39 24V40C39 40.7957 39.3161 41.5587 39.8787 42.1213C40.4413 42.6839 41.2043 43 42 43C42.7957 43 43.5587 42.6839 44.1213 42.1213C44.6839 41.5587 45 40.7957 45 40V24C45 23.2044 44.6839 22.4413 44.1213 21.8787C43.5587 21.3161 42.7957 21 42 21ZM52 17C51.2043 17 50.4413 17.3161 49.8787 17.8787C49.3161 18.4413 49 19.2044 49 20V44C49 44.7957 49.3161 45.5587 49.8787 46.1213C50.4413 46.6839 51.2043 47 52 47C52.7957 47 53.5587 46.6839 54.1213 46.1213C54.6839 45.5587 55 44.7957 55 44V20C55 19.2044 54.6839 18.4413 54.1213 17.8787C53.5587 17.3161 52.7957 17 52 17Z"
        fill="currentColor"
      />
    </svg>
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
    <div
      ref={ref}
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-black text-white"
    >
      {/* breathing animation CSS — kept local to this component */}
      <style>{`
        :root{
          --neon-c: 0, 255, 255; /* cyan neon color (R,G,B) */
        }

        @keyframes breathe {
          0% {
            transform: translateZ(0) scale(1);
            box-shadow:
              0 0 6px rgba(var(--neon-c), 0.22),
              0 0 18px rgba(var(--neon-c), 0.08);
            filter: drop-shadow(0 0 6px rgba(var(--neon-c), 0.18));
          }
          50% {
            transform: translateZ(0) scale(1.04);
            box-shadow:
              0 0 20px rgba(var(--neon-c), 0.45),
              0 0 40px rgba(var(--neon-c), 0.18);
            filter: drop-shadow(0 0 14px rgba(var(--neon-c), 0.35));
          }
          100% {
            transform: translateZ(0) scale(1);
            box-shadow:
              0 0 6px rgba(var(--neon-c), 0.22),
              0 0 18px rgba(var(--neon-c), 0.08);
            filter: drop-shadow(0 0 6px rgba(var(--neon-c), 0.18));
          }
        }

        .neon-breathe {
          /* the animation creates subtle scale + glow 'breathing' effect */
          animation: breathe 3s ease-in-out infinite;
          will-change: transform, box-shadow, filter;
          transform-origin: center;
          transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
          /* ensure the neon glow sits above the background */
          z-index: 30;
        }

        .neon-breathe:hover {
          /* slightly intensify glow on hover */
          animation-duration: 2.2s;
          transform: scale(1.045);
          box-shadow:
            0 0 28px rgba(var(--neon-c), 0.58),
            0 0 60px rgba(var(--neon-c), 0.22);
          filter: drop-shadow(0 0 18px rgba(var(--neon-c), 0.45));
        }

        /* small accessibility-friendly reduced-motion fallback */
        @media (prefers-reduced-motion: reduce) {
          .neon-breathe { animation: none; transform: none; box-shadow: 0 0 10px rgba(var(--neon-c),0.22); }
        }
      `}</style>

      <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_center,rgba(0,255,255,0.4),transparent_60%)]" />

      <section className="relative z-20 flex flex-col items-center justify-center text-center p-6 backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 shadow-[0_0_20px_rgba(0,255,255,0.25)]">
        <WelcomeImage />

        <p className="text-cyan-200 max-w-prose pt-1 leading-7 font-semibold tracking-wide drop-shadow-[0_0_6px_rgba(0,255,255,0.6)]">
          Chat live with your voice AI agent
        </p>

        <Button
          variant="primary"
          size="lg"
          onClick={onStartCall}
          className="mt-6 w-72 font-mono tracking-wider text-lg py-4 rounded-xl
            bg-cyan-500/20 border border-cyan-300/40
            hover:bg-cyan-300/30 transition-all duration-200 neon-breathe"
        >
          {startButtonText}
        </Button>
      </section>

      <div className="absolute bottom-5 left-0 flex w-full items-center justify-center z-20">
        <p className="text-gray-400 text-xs md:text-sm leading-5 font-light">
          Need help getting set up? Check out the{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="underline text-cyan-300 hover:text-cyan-200 transition-colors"
          >
            Voice AI quickstart
          </a>
          .
        </p>
      </div>
    </div>
  );
};
