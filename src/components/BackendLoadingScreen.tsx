import { useState, useEffect } from 'react';

const loadingMessages = [
  "Connexion au backend en cours...",
  "Réveil des neurones artificiels",
  "Chargement des super-pouvoirs IA",
  "Le RAG fait ses étirements matinaux",
  "Les embeddings se réchauffent",
  "GPT-4o-mini se prépare pour l'action",
  "Le vector store organise ses pensées",
  "Activation du mode compliance expert",
  "Les documents attendent leur tour",
  "L'IA apprend à être plus intelligente",
  "Optimisation des requêtes magiques",
  "Le backend se réveille doucement",
  "Chargement des compétences réglementaires",
  "Les chunks sont prêts à briller",
  "Préparation de la réponse parfaite",
];

export function BackendLoadingScreen() {
  const [currentMessage, setCurrentMessage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessage((prev) => (prev + 1) % loadingMessages.length);
    }, 2000); // Change message every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-[#0066FF] via-[#00D4FF] to-[#0066FF] relative overflow-hidden">
      {/* Animated background effects */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white/30 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-white/30 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-white/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '0.5s' }}></div>
      </div>

      {/* Main content - perfectly centered */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen">
        {/* Animated circle loader */}
        <div className="relative mb-8">
          <div className="w-24 h-24">
            <div className="absolute inset-0 border-4 border-white/30 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-transparent border-t-white rounded-full animate-spin"></div>
            <div className="absolute inset-0 border-4 border-transparent border-r-white/50 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
          </div>
        </div>

        {/* Loading message */}
        <div className="min-h-[2rem] flex items-center justify-center">
          <p className="text-white text-xl font-medium drop-shadow-lg animate-fade-in">
            {loadingMessages[currentMessage]}
          </p>
        </div>
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
}


