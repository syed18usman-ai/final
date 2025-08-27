import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChatBubbleLeftIcon, DocumentTextIcon, HomeIcon } from '@heroicons/react/24/outline';

interface LayoutProps {
  children: ReactNode;
}

const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: HomeIcon, label: 'Home' },
    { path: '/chat', icon: ChatBubbleLeftIcon, label: 'Chat' },
    { path: '/pdfs', icon: DocumentTextIcon, label: 'PDFs' }
  ];

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex items-center justify-between">
        <div className="text-xl font-bold">VTU Study Assistant</div>
        <div className="flex space-x-6">
          {navItems.map(({ path, icon: Icon, label }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md ${
                location.pathname === path
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-300 hover:bg-gray-700'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
};
