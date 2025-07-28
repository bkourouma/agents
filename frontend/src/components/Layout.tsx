import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import TenantHeader from './TenantHeader';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    { name: 'Stats', href: '/dashboard', icon: '📊' },
    { name: 'Chat', href: '/chat', icon: '💬' },
    { name: 'Agents', href: '/agents', icon: '🤖' },
    { name: 'Base de données', href: '/database-chat', icon: '🗄️' },
    { name: 'Assurance', href: '/assurance', icon: '🛡️' },
    { name: 'Devis', href: '/devis', icon: '📋' },
    { name: 'Conversations', href: '/conversations', icon: '📝' },
    { name: 'Fichiers', href: '/file-upload', icon: '📁' },
  ];

  const isActive = (href: string) => location.pathname === href;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      {/* Tab-Style Navigation */}
      <nav className="bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800 shadow-2xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
                <span className="text-white text-xs font-bold">AI</span>
              </div>
              <span className="text-white text-lg font-bold">Agents IA</span>
            </div>

            {/* Tab Navigation */}
            <div className="hidden md:flex items-center bg-slate-600/50 rounded-full p-1 backdrop-blur-sm border border-slate-500/30">
              {navigation.map((item, index) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    relative px-4 py-2 rounded-full text-xs font-medium transition-all duration-300 flex items-center space-x-1.5
                    ${isActive(item.href)
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/25'
                      : 'text-slate-300 hover:text-white hover:bg-slate-500/50'
                    }
                  `}
                >
                  <span className="text-sm">{item.icon}</span>
                  <span>{item.name}</span>

                  {/* Active glow effect */}
                  {isActive(item.href) && (
                    <div className="absolute inset-0 rounded-full bg-blue-400/20 blur-sm"></div>
                  )}
                </Link>
              ))}
            </div>

            {/* User Section */}
            <div className="flex items-center space-x-4">
              {/* User Info */}
              <div className="hidden lg:flex items-center space-x-2 text-slate-300">
                <span className="text-xs">Bienvenue, {user?.username || 'Utilisateur'}</span>
                <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">
                    {(user?.username || 'U').charAt(0).toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Logout Button */}
              <button
                onClick={logout}
                className="hidden lg:block px-3 py-1.5 bg-slate-600/50 text-slate-300 rounded-full text-xs font-medium hover:bg-red-500 hover:text-white transition-all duration-300 border border-slate-500/30 hover:border-red-400"
              >
                Se déconnecter
              </button>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-600/50 transition-all duration-300"
              >
                {mobileMenuOpen ? (
                  <XMarkIcon className="h-6 w-6" />
                ) : (
                  <Bars3Icon className="h-6 w-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-600/50 bg-slate-800">
            <div className="px-4 py-4 space-y-2">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`
                    flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-300
                    ${isActive(item.href)
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                    }
                  `}
                >
                  <span className="text-sm">{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              ))}

              {/* Mobile User Section */}
              <div className="pt-4 border-t border-slate-600/50 space-y-3">
                <div className="flex items-center space-x-2 px-3 py-2 text-slate-300">
                  <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">
                      {(user?.username || 'U').charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-xs">Bienvenue, {user?.username || 'Utilisateur'}</span>
                </div>

                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full px-3 py-2 text-left text-xs font-medium text-slate-300 hover:text-white hover:bg-red-500 transition-all duration-300 rounded-lg"
                >
                  Se déconnecter
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Tenant Header */}
      <TenantHeader />

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="animate-fadeIn">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
