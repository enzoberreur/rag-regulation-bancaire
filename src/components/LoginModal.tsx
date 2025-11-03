import { useState } from 'react';
import {
  Dialog,
  DialogContent,
} from './ui/dialog';
import { Input } from './ui/input';
import { Button } from './ui/button';

interface LoginModalProps {
  isOpen: boolean;
  onLogin: () => void;
}

export function LoginModal({ isOpen, onLogin }: LoginModalProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (username === 'enzo.berreur@gmail.com' && password === '1234567') {
      onLogin();
    } else {
      setError('Email ou mot de passe incorrect');
    }
  };

  return (
    <>
      <style>{`
        [data-slot="dialog-overlay"] {
          background: linear-gradient(to bottom, #F0F4F8, #E0E8F0) !important;
        }
      `}</style>
      <Dialog open={isOpen} onOpenChange={() => {}} modal={true}>
        <DialogContent 
          className="max-w-[30vw] bg-white border border-neutral-200 shadow-lg !p-0 overflow-hidden rounded-lg my-8 mx-4 sm:mx-8 gap-0 [&>button]:hidden [&_button]:hidden" 
          onInteractOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
        >
        <div className="p-6">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-[#0066FF] flex items-center justify-center">
                <span className="text-white font-bold text-sm">H</span>
              </div>
              <span className="text-lg font-semibold text-neutral-900">HexaBank</span>
            </div>
            <h2 className="text-xl font-bold text-neutral-800">Login</h2>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div className="space-y-2">
              <label className="text-sm font-normal text-neutral-600 block">
                User name
              </label>
              <Input
                type="text"
                placeholder="i.e banksy82"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="h-11 border-neutral-300 bg-white focus:border-neutral-400 focus:ring-0 rounded-md"
                required
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="text-sm font-normal text-neutral-600 block">
                Password
              </label>
              <Input
                type="password"
                placeholder=".........."
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 border-neutral-300 bg-white focus:border-neutral-400 focus:ring-0 rounded-md"
                required
              />
            </div>

            {/* Forgot Password Link */}
            <div>
              <span className="text-sm text-neutral-600">Forgot your password? </span>
              <a href="#" className="text-sm text-[#4A90E2] hover:text-[#357ABD] font-medium">
                Restore access now
              </a>
            </div>

            {error && (
              <div className="text-xs text-red-600 text-center py-2 px-3 bg-red-50 rounded-md border border-red-100">
                {error}
              </div>
            )}

            {/* Login Button */}
            <Button
              type="submit"
              className="w-full bg-[#5DADE2] hover:bg-[#4A90E2] text-white h-11 font-semibold rounded-lg transition-colors"
            >
              Login
            </Button>

            {/* Sign Up Link */}
            <div className="text-center pt-2">
              <span className="text-sm text-neutral-400">Don't have an account? </span>
              <a href="#" className="text-sm text-[#4A90E2] hover:text-[#357ABD] font-medium">
                Sign Up
              </a>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
    </>
  );
}
