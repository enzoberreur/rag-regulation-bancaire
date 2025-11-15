import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './ui/dropdown-menu';
import { Avatar, AvatarImage, AvatarFallback } from './ui/avatar';
import { LogOut, HelpCircle } from 'lucide-react';

interface UserProfileProps {
  onLogout: () => void;
  onRestartTour?: () => void;
}

export function UserProfile({ onLogout, onRestartTour }: UserProfileProps) {
  const handleLogout = () => {
    onLogout();
  };
  
  const handleRestartTour = () => {
    if (onRestartTour) {
      onRestartTour();
    }
  };

  return (
    <div className="w-full" data-tour="profile">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex items-center gap-3 w-full px-2 py-2 rounded-lg hover:bg-neutral-100 transition-colors group">
            <div className="flex-shrink-0" style={{ width: '40px', height: '40px' }}>
              <Avatar 
                className="border border-neutral-200 group-hover:border-[#0066FF]/50 transition-colors"
                style={{ width: '40px', height: '40px', minWidth: '40px', minHeight: '40px', maxWidth: '40px', maxHeight: '40px', borderRadius: '50%' }}
              >
                <AvatarImage src="/images/profile.jpg" />
                <AvatarFallback className="bg-[#0066FF] text-white text-sm font-medium">
                  EB
                </AvatarFallback>
              </Avatar>
            </div>
            <div className="flex flex-col items-start justify-center flex-1 min-w-0">
              <span className="text-sm font-medium text-neutral-900 truncate w-full">Enzo Berreur</span>
              <span className="text-xs text-neutral-500 truncate w-full">Chief Compliance Officer</span>
            </div>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-48">
          <div className="px-2 py-1.5 border-b border-neutral-100">
            <div className="text-sm font-medium text-neutral-900">Enzo Berreur</div>
            <div className="text-xs text-neutral-500">enzo.berreur@gmail.com</div>
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem 
            className="cursor-pointer text-[#0066FF] focus:text-[#0066FF] focus:bg-[#E6F0FF]"
            onClick={handleRestartTour}
          >
            <HelpCircle className="w-4 h-4 mr-2" />
            <span>Restart Tour</span>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem 
            className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50"
            onClick={handleLogout}
          >
            <LogOut className="w-4 h-4 mr-2" />
            <span>Se déconnecter</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
