import { Button } from '@/components/livekit/button';
import { useState } from 'react';

// Sample JSON catalog
const products = [
  { id: 'tshirt_basic', name: 'Basic T-Shirt', price: 14.99, description: 'A soft cotton t-shirt available in multiple colors.' },
  { id: 'hoodie_classic', name: 'Classic Hoodie', price: 34.99, description: 'A warm fleece hoodie perfect for everyday wear.' },
  { id: 'sneaker_white', name: 'White Sneakers', price: 49.99, description: 'Clean white sneakers with lightweight comfort.' },
  { id: 'smart_watch_pro', name: 'Smart Watch Pro', price: 599.99, description: 'High-end smartwatch with health tracking, GPS, and cellular connectivity.' },
  { id: 'luxury_leather_jacket', name: 'Luxury Leather Jacket', price: 799.99, description: 'Premium leather jacket with refined craftsmanship.' },
  { id: 'designer_handbag', name: 'Designer Handbag', price: 1200.00, description: 'Exclusive designer handbag made from genuine leather.' },
  { id: 'premium_laptop', name: 'Premium Laptop', price: 1499.99, description: 'High-performance laptop with powerful CPU, graphics, and display.' },
  { id: '4k_tv_smart', name: '4K Smart TV', price: 999.99, description: 'Ultra HD 4K smart TV with streaming and voice control.' },
  { id: 'gaming_console_x', name: 'Gaming Console X', price: 699.99, description: 'Next-gen gaming console with 4K resolution and fast loading times.' },
  { id: 'high_end_camera', name: 'High-End DSLR Camera', price: 1899.99, description: 'Professional DSLR camera with interchangeable lenses and 4K video recording.' },
];

function WelcomeImage() {
  return (
    <svg
      width="96"
      height="96"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-indigo-400 mb-6 size-28 drop-shadow-[0_0_20px_rgba(99,102,241,0.8)] animate-pulse"
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
  ref
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [cart, setCart] = useState<string[]>([]);

  const addToCart = (id: string) => {
    setCart((prev) => [...prev, id]);
  };

  return (
    <div
      ref={ref}
      className="min-h-screen bg-gradient-to-br from-[#0b0f19] via-[#111827] to-[#1f2937] flex flex-col relative overflow-hidden"
    >
      {/* FX BACKGROUND */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.25),transparent_70%)]" />
      <div className="pointer-events-none absolute inset-0 mix-blend-screen opacity-30 blur-3xl bg-[conic-gradient(from_180deg_at_50%_50%,#4f46e5,#9333ea,#4f46e5)] animate-spin-slow" />

      {/* CONTENT */}
      <section className="flex flex-col items-center justify-center text-center py-24 px-8 relative z-10 animate-fade-in">
        <WelcomeImage />

        <p className="text-indigo-300 max-w-prose pt-2 leading-7 font-bold text-3xl drop-shadow-[0_0_12px_rgba(99,102,241,0.8)] tracking-wide">
          Enter The Realm  
          <br />
          Your Voice Game Master Awaits
        </p>

        <p className="text-indigo-200/80 max-w-md mt-3 text-sm md:text-base leading-relaxed opacity-90">
          Begin your journey through immersive missions, tactical battles,
          and dynamic story-driven adventures controlled entirely by your voice.
        </p>

        <Button
          variant="primary"
          size="lg"
          onClick={onStartCall}
          className="mt-8 w-64 font-mono rounded-2xl shadow-[0_0_25px_rgba(99,102,241,0.6)] 
                     hover:shadow-[0_0_40px_rgba(129,140,248,0.9)] hover:scale-110 
                     transition-all duration-300 bg-indigo-600 hover:bg-indigo-500 text-indigo-50"
        >
          {startButtonText}
        </Button>
      </section>

      {/* PRODUCT CATALOG */}
      <section className="flex-1 overflow-y-auto px-6 py-12 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 z-10 relative">
        {products.map((product) => (
          <div
            key={product.id}
            className="bg-gray-800/70 p-4 rounded-xl flex flex-col justify-between shadow-lg hover:scale-105 transition-transform"
          >
            <h3 className="text-indigo-300 font-semibold text-lg">{product.name}</h3>
            <p className="text-gray-300 text-sm mt-1">{product.description}</p>
            <p className="text-indigo-400 font-bold mt-2">${product.price.toFixed(2)}</p>
            <Button
              variant="primary"
              size="sm"
              onClick={() => addToCart(product.id)}
              className="mt-3 w-full font-mono rounded-xl text-indigo-50"
            >
              {cart.includes(product.id) ? 'Added' : 'Buy'}
            </Button>
          </div>
        ))}
      </section>

      {/* FOOTER */}
      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center z-10">
        <p className="text-indigo-300/70 max-w-prose text-xs md:text-sm font-normal">
          Need help configuring your Game Master? Explore the{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="underline font-semibold text-indigo-400 hover:text-indigo-300"
          >
            Voice AI Quickstart
          </a>.
        </p>
      </div>
    </div>
  );
};
