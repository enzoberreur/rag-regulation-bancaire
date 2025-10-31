import { useEffect, useState } from 'react';

interface LoadingAnimationProps {
  variant?: 'dots' | 'wave' | 'cursor';
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export function LoadingAnimation({ 
  variant = 'dots', 
  size = 'md',
  color = '#0066FF'
}: LoadingAnimationProps) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhase((prev) => (prev + 1) % 3);
    }, 600);
    return () => clearInterval(interval);
  }, []);

  if (variant === 'cursor') {
    return (
      <span className="inline-block ml-1 relative">
        <span 
          className="inline-block w-[2px] h-4 bg-current"
          style={{
            animation: 'typing-cursor 1.2s ease-in-out infinite',
            color: color
          }}
        />
        <style>{`
          @keyframes typing-cursor {
            0%, 45% { opacity: 1; }
            46%, 100% { opacity: 0.3; }
          }
        `}</style>
      </span>
    );
  }

  if (variant === 'wave') {
    const waveSize = size === 'sm' ? 'w-1 h-1' : size === 'md' ? 'w-1.5 h-1.5' : 'w-2 h-2';
    const waveGap = size === 'sm' ? 'gap-1' : size === 'md' ? 'gap-1.5' : 'gap-2';
    
    return (
      <div className={`flex items-center ${waveGap}`}>
        {[0, 1, 2].map((i) => {
          const delay = i * 0.2;
          const isActive = phase === i;
          const isNext = phase === (i + 1) % 3;
          
          return (
            <div
              key={i}
              className={`${waveSize} rounded-full`}
              style={{
                backgroundColor: color,
                opacity: isActive ? 0.4 : isNext ? 0.75 : 1,
                transform: `scale(${isActive ? 1 : isNext ? 1.25 : 1.15})`,
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                animationDelay: `${delay}s`,
              }}
            />
          );
        })}
      </div>
    );
  }

  // Default: dots variant with elegant fade and lift
  const dotSize = size === 'sm' ? 'w-1.5 h-1.5' : size === 'md' ? 'w-2 h-2' : 'w-2.5 h-2.5';
  const dotGap = size === 'sm' ? 'gap-1.5' : size === 'md' ? 'gap-2' : 'gap-2.5';
  
  return (
    <div className={`flex items-center ${dotGap}`}>
      {[0, 1, 2].map((i) => {
        const delay = i * 0.15;
        const isActive = phase === i;
        const isNext = phase === (i + 1) % 3;
        
        return (
          <div
            key={i}
            className={`${dotSize} rounded-full`}
            style={{
              backgroundColor: color,
              opacity: isActive ? 0.25 : isNext ? 0.5 : 1,
              transform: `translateY(${isActive ? '0px' : isNext ? '-3px' : '-6px'}) scale(${isActive ? 1 : isNext ? 1.1 : 1.2})`,
              transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
              animationDelay: `${delay}s`,
            }}
          />
        );
      })}
    </div>
  );
}

