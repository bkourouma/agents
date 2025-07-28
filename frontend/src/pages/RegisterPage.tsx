import React from 'react';

const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Créez votre compte
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Plateforme d'Agents IA
          </p>
        </div>
        <div className="bg-white py-8 px-6 shadow rounded-lg">
          <p className="text-center text-gray-500">
            Formulaire d'inscription bientôt disponible...
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
