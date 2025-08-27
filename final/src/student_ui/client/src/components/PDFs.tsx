import { useEffect, useState } from 'react';
import { useStore } from '../services/state';
import { DocumentTextIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { downloadFile } from '../utils/helpers';

interface PDF {
  id: string;
  name: string;
  subject: string;
  size: number;
}

export const PDFs = () => {
  const { currentSemester, fetchSubjects, subjects, fetchPDFs } = useStore();
  const [selectedSubject, setSelectedSubject] = useState<string>('');
  const [pdfs, setPdfs] = useState<PDF[]>([]);

  useEffect(() => {
    if (currentSemester) {
      fetchSubjects(currentSemester);
    }
  }, [currentSemester, fetchSubjects]);

  useEffect(() => {
    if (selectedSubject) {
      const loadPDFs = async () => {
        const files = await fetchPDFs(currentSemester, selectedSubject);
        setPdfs(files);
      };
      loadPDFs();
    }
  }, [selectedSubject, currentSemester, fetchPDFs]);

  if (!currentSemester) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-600">Please select a semester from the home page first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Study Materials</h2>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Subject
          </label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="w-full rounded-md border border-gray-300 p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Choose a subject...</option>
            {subjects.map((subject) => (
              <option key={subject} value={subject}>
                {subject}
              </option>
            ))}
          </select>
        </div>

        {selectedSubject && (
          <div className="space-y-4">
            {pdfs.length === 0 ? (
              <p className="text-gray-600 text-center py-4">
                No PDFs available for this subject.
              </p>
            ) : (
              pdfs.map((pdf) => (
                <div
                  key={pdf.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-4">
                    <DocumentTextIcon className="h-8 w-8 text-blue-600" />
                    <div>
                      <h3 className="font-medium text-gray-900">{pdf.name}</h3>
                      <p className="text-sm text-gray-500">{pdf.size} KB</p>
                    </div>
                  </div>
                  <button
                    onClick={() => downloadFile(pdf.id, pdf.name)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    <ArrowDownTrayIcon className="h-5 w-5" />
                    <span>Download</span>
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
