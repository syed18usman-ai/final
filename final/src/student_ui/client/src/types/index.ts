// Types for the API responses
export interface ApiResponse<T> {
    success: boolean;
    error?: string;
    data?: T;
}

export interface PDFFile {
    file_path: string;
    file_size: number;
    book_title: string;
    subject: string | null;
    semester: string | null;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
}

export interface ChatResponse {
    response: string;
    sources: string[];
    images: string[];
    chat_history: ChatMessage[];
}

// State interfaces
export interface AppState {
    currentPage: 'home' | 'chat' | 'pdfs';
    currentSemester: string | null;
    currentSubject: string | null;
    chatHistory: ChatMessage[];
    pdfs: PDFFile[];
    isLoading: boolean;
    error: string | null;
}
