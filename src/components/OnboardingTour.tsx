import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  element: string; // CSS selector
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
  icon?: string;
}

const steps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to RAG Banking Assistant',
    description: 'Your AI-powered companion for regulatory compliance analysis. Let\'s explore the key features together.',
    element: '',
    position: 'center',
  },
  {
    id: 'sidebar',
    title: 'Session History',
    description: 'Manage your analysis sessions. Each conversation is automatically saved and organized here.',
    element: '[data-tour="sidebar"]',
    position: 'right',
  },
  {
    id: 'new-session',
    title: 'Create Session',
    description: 'Start a fresh conversation to explore different regulatory topics independently.',
    element: '[data-tour="new-session"]',
    position: 'right',
  },
  {
    id: 'documents',
    title: 'Upload Documents',
    description: 'Add PDF documents for intelligent semantic search with automatic text extraction and chunking.',
    element: '[data-tour="document-upload"]',
    position: 'right',
  },
  {
    id: 'chat-input',
    title: 'Ask Questions',
    description: 'Type complex regulatory queries. The system retrieves relevant context and generates detailed answers with citations.',
    element: '[data-tour="chat-input"]',
    position: 'top',
  },
  {
    id: 'example-questions',
    title: 'Example Queries',
    description: 'Try these pre-configured questions to explore MREL, CET1, and TLAC regulatory frameworks.',
    element: '[data-tour="example-questions"]',
    position: 'top',
  },
  {
    id: 'citations',
    title: 'Source Citations',
    description: 'Answers include highlighted citations. Hover to see document names and page numbers.',
    element: '[data-tour="chat-messages"]',
    position: 'left',
  },
  {
    id: 'observability',
    title: 'System Metrics',
    description: 'Monitor response times, token usage, and citation quality in real-time.',
    element: '[data-tour="observability"]',
    position: 'top',
  },
  {
    id: 'ready',
    title: 'You\'re Ready',
    description: 'Start analyzing CRD4 regulations with AI-powered semantic search and precise citations.',
    element: '',
    position: 'center',
  },
];

interface OnboardingTourProps {
  isOpen: boolean;
  onComplete: () => void;
}

export function OnboardingTour({ isOpen, onComplete }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [spotlightPosition, setSpotlightPosition] = useState({ top: 0, left: 0, width: 0, height: 0 });
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  console.log('OnboardingTour render - isOpen:', isOpen, 'currentStep:', currentStep);

  const step = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;
  const isCenterStep = step.position === 'center';

  // Reset to first step when tour is opened
  useEffect(() => {
    console.log('OnboardingTour useEffect - isOpen changed to:', isOpen);
    if (isOpen) {
      console.log('Resetting currentStep to 0');
      setCurrentStep(0);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !step.element) return;

    const updatePosition = () => {
      const element = document.querySelector(step.element);
      if (!element) {
        console.warn(`Element not found: ${step.element}`);
        return;
      }

      const rect = element.getBoundingClientRect();
      const padding = 12;

      setSpotlightPosition({
        top: rect.top - padding,
        left: rect.left - padding,
        width: rect.width + padding * 2,
        height: rect.height + padding * 2,
      });

      // Calculate tooltip position based on step.position
      const tooltipWidth = 420;
      const tooltipHeight = 200;
      const gap = 20;
      const viewportPadding = 20;
      let top = 0;
      let left = 0;
      let finalPosition = step.position;

      // Try primary position
      switch (step.position) {
        case 'top':
          top = rect.top - tooltipHeight - gap;
          left = rect.left + rect.width / 2 - tooltipWidth / 2;
          // If doesn't fit on top, switch to bottom
          if (top < viewportPadding) {
            top = rect.bottom + gap;
            finalPosition = 'bottom';
          }
          break;
        case 'bottom':
          top = rect.bottom + gap;
          left = rect.left + rect.width / 2 - tooltipWidth / 2;
          // If doesn't fit on bottom, switch to top
          if (top + tooltipHeight > window.innerHeight - viewportPadding) {
            top = rect.top - tooltipHeight - gap;
            finalPosition = 'top';
          }
          break;
        case 'left':
          top = rect.top + rect.height / 2 - tooltipHeight / 2;
          left = rect.left - tooltipWidth - gap;
          // If doesn't fit on left, switch to right
          if (left < viewportPadding) {
            left = rect.right + gap;
            finalPosition = 'right';
          }
          break;
        case 'right':
          top = rect.top + rect.height / 2 - tooltipHeight / 2;
          left = rect.right + gap;
          // If doesn't fit on right, switch to left
          if (left + tooltipWidth > window.innerWidth - viewportPadding) {
            left = rect.left - tooltipWidth - gap;
            finalPosition = 'left';
          }
          break;
      }

      // Final safety check - keep tooltip fully in viewport
      top = Math.max(viewportPadding, Math.min(top, window.innerHeight - tooltipHeight - viewportPadding));
      left = Math.max(viewportPadding, Math.min(left, window.innerWidth - tooltipWidth - viewportPadding));

      setTooltipPosition({ top, left });
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition, true);

    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [isOpen, currentStep, step.element, step.position]);

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSkip = () => {
    onComplete();
  };
  
  // Handle ESC key to skip tour
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleSkip();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[9999]"
          style={{ pointerEvents: 'none' }}
        >
        {/* Dark overlay with hole for spotlight */}
        <svg
          className="absolute inset-0 w-full h-full"
          style={{ pointerEvents: 'none' }}
        >
          <defs>
            <mask id="spotlight-mask">
              <rect x="0" y="0" width="100%" height="100%" fill="white" />
              {!isCenterStep && step.element && (
                <motion.rect
                  initial={{ opacity: 0 }}
                  animate={{
                    x: spotlightPosition.left,
                    y: spotlightPosition.top,
                    width: spotlightPosition.width,
                    height: spotlightPosition.height,
                    opacity: 1,
                  }}
                  transition={{ duration: 0.4, ease: 'easeInOut' }}
                  rx="12"
                  fill="black"
                />
              )}
            </mask>
          </defs>
          <rect
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="rgba(0, 0, 0, 0.6)"
            mask="url(#spotlight-mask)"
          />
        </svg>

        {/* Animated border around highlighted element */}
        {!isCenterStep && step.element && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{
              opacity: 1,
              scale: 1,
              top: spotlightPosition.top,
              left: spotlightPosition.left,
              width: spotlightPosition.width,
              height: spotlightPosition.height,
            }}
            transition={{ duration: 0.4, ease: 'easeInOut' }}
            className="absolute rounded-xl border-2 border-[#0066FF] shadow-lg"
            style={{ pointerEvents: 'none' }}
          />
        )}

        {/* Tooltip */}
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{
            opacity: 1,
            scale: 1,
            y: 0,
            ...(isCenterStep
              ? { top: '50%', left: '50%', x: '-50%', y: '-50%' }
              : { top: tooltipPosition.top, left: tooltipPosition.left }),
          }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="absolute bg-white rounded-lg shadow-xl border border-neutral-200 overflow-hidden"
          style={{
            width: isCenterStep ? '520px' : '420px',
            maxWidth: '90vw',
            pointerEvents: 'auto',
          }}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-neutral-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-neutral-400">
                {currentStep + 1}/{steps.length}
              </span>
              <button
                onClick={handleSkip}
                className="text-xs text-neutral-400 hover:text-neutral-600 transition-colors"
              >
                Skip
              </button>
            </div>
            <h3 className="text-base font-semibold text-neutral-900">{step.title}</h3>
          </div>

          {/* Content */}
          <div className="px-6 py-5">
            <p className="text-sm text-neutral-600 leading-relaxed">
              {step.description}
            </p>
          </div>

          {/* Footer actions */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-neutral-100">
            <button
              onClick={handlePrevious}
              disabled={isFirstStep}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                isFirstStep
                  ? 'text-neutral-300 cursor-not-allowed'
                  : 'text-neutral-600 hover:bg-neutral-50'
              }`}
            >
              ← Back
            </button>

            <button
              onClick={handleNext}
              className="px-4 py-1.5 text-xs font-medium text-white bg-[#0066FF] hover:bg-[#0052CC] rounded transition-colors"
            >
              {isLastStep ? 'Start' : 'Next'}
            </button>
          </div>
        </motion.div>
      </motion.div>
      )}
    </AnimatePresence>
  );
}
