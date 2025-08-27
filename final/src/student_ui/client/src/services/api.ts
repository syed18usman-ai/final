import { ApiResponse, ChatMessage, ChatResponse, PDFFile } from '../types';

class APIService {
    private static instance: APIService;
    private baseUrl: string = '/api';

    private constructor() {}

    static getInstance(): APIService {
        if (!APIService.instance) {
            APIService.instance = new APIService();
        }
        return APIService.instance;
    }

    private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
        if (!response.ok) {
            const error = await response.text();
            throw new Error(error);
        }
        return await response.json();
    }

    async sendChatMessage(
        message: string,
        chatHistory: ChatMessage[],
        semester?: string,
        subject?: string
    ): Promise<ApiResponse<ChatResponse>> {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('chat_history', JSON.stringify(chatHistory));
        formData.append('include_images', 'true');
        if (semester) formData.append('semester', semester);
        if (subject) formData.append('subject', subject);

        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            body: formData,
        });

        return this.handleResponse<ChatResponse>(response);
    }

    async getPDFs(semester?: string, subject?: string): Promise<ApiResponse<PDFFile[]>> {
        let url = `${this.baseUrl}/pdfs`;
        if (semester) {
            url += `?semester=${encodeURIComponent(semester)}`;
            if (subject) {
                url += `&subject=${encodeURIComponent(subject)}`;
            }
        }

        const response = await fetch(url);
        return this.handleResponse<PDFFile[]>(response);
    }

    async getSemesters(): Promise<ApiResponse<string[]>> {
        const response = await fetch(`${this.baseUrl}/semesters`);
        return this.handleResponse<string[]>(response);
    }

    async getSubjects(semester: string): Promise<ApiResponse<string[]>> {
        const response = await fetch(`${this.baseUrl}/subjects/${encodeURIComponent(semester)}`);
        return this.handleResponse<string[]>(response);
    }

    async downloadPDF(filePath: string): Promise<Blob> {
        const response = await fetch(`${this.baseUrl}/pdfs/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ file_path: filePath }),
        });

        if (!response.ok) {
            throw new Error('Failed to download PDF');
        }

        return await response.blob();
    }
}

export const api = APIService.getInstance();
