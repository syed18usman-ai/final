import { FormEvent, useEffect, useRef } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';
import { useStore } from '../services/state';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const Chat = () => {
  const { messages, sendMessage, isLoading } = useStore();
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const message = inputRef.current?.value.trim();
    
    if (!message || isLoading) return;
    
    await sendMessage(message);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col bg-white rounded-lg shadow-md">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message: Message, index: number) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t p-4">
        <div className="flex space-x-4">
          <textarea
            ref={inputRef}
            className="flex-1 resize-none rounded-lg border p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Type your message..."
            rows={2}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className={`rounded-lg px-4 py-2 ${
              isLoading
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white`}
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
};
