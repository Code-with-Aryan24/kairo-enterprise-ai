import { Bell, Search, CircleUserRound, Menu } from "lucide-react";

function Header({ onMenuClick }) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="rounded-md p-2 text-slate-600 hover:bg-slate-100 md:hidden"
          aria-label="Open navigation"
        >
          <Menu size={21} />
        </button>

        <div className="flex items-center gap-3 text-slate-400">
          <Search size={19} />
          <span className="hidden text-sm sm:block">
            Search KAIRO...
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4 sm:gap-5">
        <button
          className="text-slate-500 transition hover:text-slate-900"
          aria-label="Notifications"
        >
          <Bell size={19} />
        </button>

        <div className="flex items-center gap-2">
          <CircleUserRound size={24} className="text-slate-600" />

          <div className="hidden text-left sm:block">
            <p className="text-sm font-medium text-slate-900">
              KAIRO User
            </p>
            <p className="text-xs text-slate-500">
              Enterprise Workspace
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;