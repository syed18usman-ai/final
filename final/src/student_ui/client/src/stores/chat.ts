import { create } from 'zustand'
import axios from 'axios'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  images?: string[]
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  currentSemester: string | null
  currentSubject: string | null
  error: string | null
  addMessage: (message: Message) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  sendMessage: (content: string) => Promise<void>
  clearChat: () => void
  setContext: (semester: string | null, subject: string | null) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  currentSemester: null,
  currentSubject: null,
  error: null,

  addMessage: (message) => 
    set((state) => ({ messages: [...state.messages, message] })),

  setLoading: (loading) => 
    set({ isLoading: loading }),

  setError: (error) => 
    set({ error }),

  sendMessage: async (content) => {
    const state = get()
    set({ isLoading: true, error: null })

    try {
      const formData = new FormData()
      formData.append('message', content)
      formData.append('chat_history', JSON.stringify(state.messages))
      formData.append('include_images', 'true')
      
      if (state.currentSemester) {
        formData.append('semester', state.currentSemester)
      }
      if (state.currentSubject) {
        formData.append('subject', state.currentSubject)
      }

      const response = await axios.post<{
        success: boolean
        response: string
        sources: string[]
        images: string[]
      }>('/api/chat', formData)

      if (response.data.success) {
        set((state) => ({
          messages: [
            ...state.messages,
            {
              role: 'assistant',
              content: response.data.response,
              sources: response.data.sources,
              images: response.data.images
            }
          ]
        }))
      } else {
        throw new Error('Failed to get response from server')
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'An error occurred' })
    } finally {
      set({ isLoading: false })
    }
  },

  clearChat: () => 
    set({ messages: [] }),

  setContext: (semester, subject) => 
    set({ currentSemester: semester, currentSubject: subject })
}))
