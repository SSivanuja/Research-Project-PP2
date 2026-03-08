import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Brain, 
  GitBranch, 
  Shield, 
  FolderOpen, 
  History, 
  Settings, 
  HelpCircle,
  ChevronLeft,
  X,
  BookOpen
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  isCollapsed: boolean;
  onClose: () => void;
  onCollapse: () => void;
}

const navItems = [
  { 
    section: null,
    items: [
      { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', exact: true },
    ]
  },
  {
    section: 'PROCESSING',
    items: [
      { path: '/dashboard/analyzer', icon: FileText, label: 'Document Analyzer' },
      { path: '/dashboard/reasoning', icon: Brain, label: 'Legal Reasoning' },
      { path: '/dashboard/knowledge-graph', icon: GitBranch, label: 'Knowledge Graph' },
      { path: '/dashboard/risk-detection', icon: Shield, label: 'Risk Detection' },
    ]
  },
  {
    section: 'MANAGEMENT',
    items: [
      { path: '/dashboard/documents', icon: FolderOpen, label: 'Deed Explorer' },
      { path: '/dashboard/legal-reference', icon: BookOpen, label: 'Legal Reference' },
      { path: '/dashboard/history', icon: History, label: 'History' },
      { path: '/dashboard/settings', icon: Settings, label: 'Settings' },
    ]
  },
  {
    section: null,
    items: [
      { path: '/dashboard/help', icon: HelpCircle, label: 'Help & Support' },
    ]
  }
];

const Sidebar = ({ isOpen, isCollapsed, onClose, onCollapse }: SidebarProps) => {
  const location = useLocation();

  const isActive = (path: string, exact?: boolean) => {
    if (exact) {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed lg:static inset-y-0 left-0 z-50 flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300",
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        isCollapsed ? "w-16" : "w-60"
      )}>
        {/* Mobile close button */}
        <div className="lg:hidden flex items-center justify-end p-4 border-b border-sidebar-border">
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 scrollbar-thin">
          {navItems.map((group, groupIndex) => (
            <div key={groupIndex} className="mb-2">
              {group.section && !isCollapsed && (
                <p className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {group.section}
                </p>
              )}
              {group.section && isCollapsed && (
                <div className="mx-3 my-2 border-t border-sidebar-border" />
              )}
              
              <ul className="space-y-1 px-2">
                {group.items.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={() => window.innerWidth < 1024 && onClose()}
                      className={({ isActive: navActive }) => cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group",
                        isActive(item.path, item.exact) || navActive
                          ? "bg-sidebar-accent text-sidebar-primary font-medium border-l-2 border-sidebar-primary ml-0.5"
                          : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                        isCollapsed && "justify-center px-2"
                      )}
                    >
                      <item.icon className={cn(
                        "h-5 w-5 flex-shrink-0 transition-colors",
                        isActive(item.path, item.exact) ? "text-sidebar-primary" : "text-muted-foreground group-hover:text-sidebar-foreground"
                      )} />
                      {!isCollapsed && (
                        <span className="truncate">{item.label}</span>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Collapse button */}
        <div className="hidden lg:flex items-center justify-center p-4 border-t border-sidebar-border">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={onCollapse}
            className="h-8 w-8"
          >
            <ChevronLeft className={cn(
              "h-4 w-4 transition-transform duration-200",
              isCollapsed && "rotate-180"
            )} />
          </Button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
