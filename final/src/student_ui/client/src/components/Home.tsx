import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useStore } from '../services/state';
import { ChatBubbleLeftIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

export const Home = () => {
  const { fetchSemesters, semesters, currentSemester, setCurrentSemester } = useStore();

  useEffect(() => {
    fetchSemesters();
  }, [fetchSemesters]);

  return (
    <div className="space-y-8">
      <section className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to VTU Study Assistant</h1>
        <p className="text-gray-600 mb-6">
          Get help with your studies through our AI-powered chat assistant and access to study materials.
        </p>
        
        <div className="grid md:grid-cols-2 gap-6">
          <Link
            to="/chat"
            className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <ChatBubbleLeftIcon className="h-8 w-8 text-blue-600 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900">Chat Assistant</h3>
              <p className="text-blue-600">Get instant help with your questions</p>
            </div>
          </Link>

          <Link
            to="/pdfs"
            className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
          >
            <DocumentTextIcon className="h-8 w-8 text-green-600 mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-green-900">Study Materials</h3>
              <p className="text-green-600">Access course PDFs and resources</p>
            </div>
          </Link>
        </div>
      </section>

      <section className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Select Your Semester</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {semesters.map((semester) => (
            <button
              key={semester}
              onClick={() => setCurrentSemester(semester)}
              className={`p-4 rounded-lg text-center transition-colors ${
                currentSemester === semester
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
              }`}
            >
              {semester}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
};
