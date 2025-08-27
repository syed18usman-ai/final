import { create } from 'zustand';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface PDF {
  id: string;
  name: string;
  subject: string;
  size: number;
}

interface State {
  currentSemester: string;
  semesters: string[];
  subjects: string[];
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  setCurrentSemester: (semester: string) => void;
  fetchSemesters: () => Promise<void>;
  fetchSubjects: (semester: string) => Promise<void>;
  fetchPDFs: (semester: string, subject: string) => Promise<PDF[]>;
  sendMessage: (content: string) => Promise<void>;
}

type Store = State;

export const useStore = create<Store>((set, get) => ({
  currentSemester: '',
  semesters: [],
  subjects: [],
  messages: [],
  isLoading: false,
  error: null,

  setCurrentSemester: (semester) => {
    set({ currentSemester: semester });
  },

  fetchSemesters: async () => {
    try {
      const response = await fetch('/api/semesters');
      const semesters = await response.json();
      set({ semesters, error: null });
    } catch (error) {
      set({ error: 'Failed to fetch semesters' });
    }
  },

  fetchSubjects: async (semester) => {
    try {
      const response = await fetch(`/api/subjects/${semester}`);
      const subjects = await response.json();
      set({ subjects, error: null });
    } catch (error) {
      set({ error: 'Failed to fetch subjects' });
    }
  },

  fetchPDFs: async (semester, subject) => {
    try {
      const response = await fetch(`/api/pdfs/${semester}/${subject}`);
      const pdfs = await response.json();
      set({ error: null });
      return pdfs;
    } catch (error) {
      set({ error: 'Failed to fetch PDFs' });
      return [];
    }
  },

  sendMessage: async (content) => {
    const { messages } = get();
    const newMessage: Message = { role: 'user', content };
    
    set({ 
      messages: [...messages, newMessage],
      isLoading: true,
      error: null 
    });

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: content }),
      });
      const data = await response.json();
      set((state) => ({
        messages: [...state.messages, { role: 'assistant', content: data.message }],
        isLoading: false
      }));
    } catch (error) {
      set((state) => ({
        messages: [...state.messages, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }],
        isLoading: false,
        error: 'Failed to send message'
      }));
    }
  }
}));
