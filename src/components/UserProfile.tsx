import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './ui/dropdown-menu';
import { Avatar, AvatarImage, AvatarFallback } from './ui/avatar';
import { LogOut } from 'lucide-react';

interface UserProfileProps {
  onLogout: () => void;
}

export function UserProfile({ onLogout }: UserProfileProps) {
  const handleLogout = () => {
    onLogout();
  };

  return (
    <div className="w-full">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex items-center gap-3 w-full px-2 py-2 rounded-lg hover:bg-neutral-100 transition-colors group">
            <Avatar className="w-10 h-10 border border-neutral-200 group-hover:border-[#0066FF]/50 transition-colors flex-shrink-0">
              <AvatarImage src="/images/profile.jpg" className="object-cover" />
              <AvatarFallback className="bg-[#0066FF] text-white text-sm font-medium">
                EB
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col items-start justify-center flex-1 min-w-0">
              <span className="text-sm font-medium text-neutral-900 truncate w-full">Enzo Berreur</span>
              <span className="text-xs text-neutral-500 truncate w-full">Crackito</span>
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
